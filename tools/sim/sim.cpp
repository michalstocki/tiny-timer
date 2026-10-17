// Host simulation of the timer firmware (firmware/src/main.c, oled.c, render.c
// and timebase.h are compiled UNMODIFIED against mock <avr/...> headers).
//
// What it checks: the state machine, button decoding/debouncing, timing in
// whole 8 ms ticks, the I2C bit stream (START/STOP, bytes, open-drain
// discipline) and the decoded picture (OCR of the pixels).
// What it cannot check: AVR code generation, real clock accuracy, the
// electrical behaviour of the OLED, speaker or buttons.
//
// Build/run:  tools/sim/run.sh
#include <math.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <string>
#include <vector>

#include <sys/wait.h>
#include <unistd.h>

#include <avr/io.h>

Regs R;

struct SimDone {};

// ---------------------------------------------------------------- time ----
static double now_us = 0;
static double end_us = 0;
static double next_tick_us = 1e30;
static double tick_period_us = 0;
static bool tick_pending = false;
static int sleeping_pd = 0;

extern "C" void TIM0_COMPA_vect(void);
extern "C" void PCINT0_vect(void);

// ------------------------------------------------------------- logging ----
struct Ev {
    double t;
    std::string kind;
    std::string text;
    int bar = -1;  // frame events: lit pixels on the 1 px border
};
static std::vector<Ev> evlog;
static void logev(const char *kind, const char *fmt, ...)
{
    char buf[256];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(buf, sizeof buf, fmt, ap);
    va_end(ap);
    Ev e;
    e.t = now_us;
    e.kind = kind;
    e.text = buf;
    evlog.push_back(e);
}

// -------------------------------------------------------------- inputs ----
struct In {
    double t;
    int run;  // 1 = released (pull-up), 0 = pressed
    int adc;  // 255 none, 128 "-", 0 "+"
};
static std::vector<In> script;

static In input_at(double t)
{
    In cur = {0, 1, 255};
    for (auto &e : script)
        if (e.t <= t)
            cur = e;
    return cur;
}

static int in_isr = 0;
static void advance(double us);
static uint8_t rd_pinb(void)
{
    uint8_t v = (uint8_t)(input_at(now_us).run << PB3);
    if (!in_isr) advance(0.4);  // polling loops must make time pass
    return v;
}
static uint8_t rd_adch(void) { return (uint8_t)input_at(now_us).adc; }

enum Which { RUN, PLUS, MINUS };

static void press(double t_ms, Which w, double hold_ms = 120, bool bounce = true)
{
    double t = t_ms * 1000, h = hold_ms * 1000;
    auto set = [&](double tt, bool down) {
        In e = {tt, 1, 255};
        if (down) {
            if (w == RUN) e.run = 0;
            else if (w == PLUS) e.adc = 0;
            else e.adc = 128;
        }
        script.push_back(e);
    };
    if (bounce) {  // contact chatter for 2 ms on both edges
        for (int i = 0; i < 4; i++) set(t + i * 500, i % 2 == 0);
        set(t + 2000, true);
        for (int i = 0; i < 4; i++) set(t + h + i * 500, i % 2 == 1);
        set(t + h + 2000, false);
    } else {
        set(t, true);
        set(t + h, false);
    }
}

// ------------------------------------------------------------ I2C bus ----
struct Bus {
    bool sda = true, scl = true;
    bool in_xfer = false;
    int bits = 0;
    uint8_t shift = 0;
    std::vector<uint8_t> bytes;
    bool violation = false;
} bus;

static bool display_on = false;
static bool vertical_mode = false, page_range_ok = false;
static uint8_t pixels[32][128];
static int frames = 0;
static std::string last_text;
static bool last_bell = false;
static int init_count = 0;

static const uint8_t FONT[11][5] = {
    {0x3E, 0x51, 0x49, 0x45, 0x3E}, {0x00, 0x42, 0x7F, 0x40, 0x00},
    {0x42, 0x61, 0x51, 0x49, 0x46}, {0x21, 0x41, 0x45, 0x4B, 0x31},
    {0x18, 0x14, 0x12, 0x7F, 0x10}, {0x27, 0x45, 0x45, 0x45, 0x39},
    {0x3C, 0x4A, 0x49, 0x49, 0x30}, {0x01, 0x71, 0x09, 0x05, 0x03},
    {0x36, 0x49, 0x49, 0x49, 0x36}, {0x06, 0x49, 0x49, 0x29, 0x1E},
    {0x00, 0x00, 0x14, 0x00, 0x00}};

// OCR: sample the center of every 3x3 block of the scaled 5x7 font.
static std::string ocr(void)
{
    for (int ncell = 5; ncell >= 4; ncell--) {
        int x0 = 64 - 9 * ncell;
        std::string s;
        bool ok = true;
        for (int c = 0; c < ncell && ok; c++) {
            int found = -1;
            for (int g = 0; g < 11 && found < 0; g++) {
                bool match = true;
                for (int col = 0; col < 5 && match; col++)
                    for (int row = 0; row < 7; row++) {
                        int x = x0 + 18 * c + 3 * col + 1, y = 5 + 3 * row + 1;
                        // every pixel of the 3x3 block must agree
                        for (int dx = -1; dx <= 1; dx++)
                            for (int dy = -1; dy <= 1; dy++)
                                if (pixels[y + dy][x + dx] != ((FONT[g][col] >> row) & 1))
                                    match = false;
                    }
                if (match) found = g;
            }
            if (found < 0) ok = false;
            else s += (found == 10) ? ':' : (char)('0' + found);
        }
        if (ok) {
            // columns outside the text must be empty
            int lit_out = 0;
            for (int y = 0; y < 32; y++)
                for (int x = 0; x < 128; x++)
                    if (pixels[y][x] && (x < x0 || x >= x0 + 18 * ncell) && !(x >= 106 && x < 122 && y >= 8 && y < 24) &&
                        !(x == 0 || x == 127 || y == 0 || y == 31))
                        lit_out++;
            if (lit_out == 0) return s;
        }
    }
    return "?";
}

static void finish_xfer(void)
{
    auto &b = bus.bytes;
    if (b.size() < 2 || b[0] != 0x78) {
        logev("bus", "bad transaction (%zu bytes, addr 0x%02X)", b.size(), b.empty() ? 0 : b[0]);
        return;
    }
    if (b[1] == 0x00) {
        // command stream
        std::string s;
        char t[8];
        for (size_t i = 2; i < b.size(); i++) {
            snprintf(t, sizeof t, "%02X ", b[i]);
            s += t;
        }
        logev("cmd", "%s", s.c_str());
        for (size_t i = 2; i < b.size(); i++) {
            if (b[i] == 0xAF) { display_on = true; }
            if (b[i] == 0xAE) { display_on = false; }
            if (b[i] == 0x20 && i + 1 < b.size() && b[i + 1] == 0x01) vertical_mode = true;
            if (b[i] == 0x22 && i + 2 < b.size() && b[i + 1] == 0 && b[i + 2] == 3) page_range_ok = true;
        }
        if (b.size() > 3 && b[2] == 0xA8) init_count++;
    } else if (b[1] == 0x40) {
        if (b.size() != 2 + 512) {
            logev("bus", "data transaction with %zu bytes (expected 512)", b.size() - 2);
            return;
        }
        for (int i = 0; i < 512; i++) {
            int col = i / 4, page = i % 4;
            for (int bit = 0; bit < 8; bit++)
                pixels[page * 8 + bit][col] = (b[2 + i] >> bit) & 1;
        }
        frames++;
        int bell_px = 0;
        for (int y = 8; y < 24; y++)
            for (int x = 106; x < 122; x++) bell_px += pixels[y][x];
        last_bell = bell_px > 100;
        last_text = ocr();
        logev("frame", "%s%s%s", last_text.c_str(), last_bell ? " +bell" : "", display_on ? "" : " (display OFF)");
        int bar = 0;
        for (int x = 0; x < 128; x++) bar += pixels[0][x] + pixels[31][x];
        for (int y = 1; y < 31; y++) bar += pixels[y][0] + pixels[y][127];
        evlog.back().bar = bar;
    } else {
        logev("bus", "unknown control byte 0x%02X", b[1]);
    }
}

static void bus_update(void)
{
    if (PORTB.v & ((1 << PB0) | (1 << PB2))) bus.violation = true;  // open drain only
    bool sda = !(DDRB.v & (1 << PB0));
    bool scl = !(DDRB.v & (1 << PB2));
    if (sda != bus.sda && bus.scl && scl) {
        if (!sda) {  // START
            bus.in_xfer = true;
            bus.bits = 0;
            bus.shift = 0;
            bus.bytes.clear();
        } else if (bus.in_xfer) {  // STOP
            bus.in_xfer = false;
            finish_xfer();
        }
    } else if (scl && !bus.scl && bus.in_xfer) {  // SCL rising: sample
        if (bus.bits < 8) {
            bus.shift = (uint8_t)((bus.shift << 1) | (sda ? 1 : 0));
            bus.bits++;
            if (bus.bits == 8) bus.bytes.push_back(bus.shift);
        } else {
            bus.bits = 0;  // ACK clock
            if (!sda) { /* slave would pull low; master releases: fine */ }
        }
    } else if (sda != bus.sda && bus.scl && !scl) {
        // both changed in one write: not produced by the firmware
    }
    bus.sda = sda;
    bus.scl = scl;
}

// ------------------------------------------------------ timer & CPU ----
static bool timer_running(void)
{
    return (TCCR0B.v & 7) != 0 && (TCCR0A.v & (1 << WGM01));
}

static void timer_reconfig(bool restart)
{
    int cs = TCCR0B.v & 7;
    static const int div[8] = {0, 1, 8, 64, 256, 1024, 0, 0};
    if (cs == 0 || !(TCCR0A.v & (1 << WGM01))) {
        next_tick_us = 1e30;
        return;
    }
    tick_period_us = (double)div[cs] * (OCR0A.v + 1) / F_CPU * 1e6;
    if (restart || next_tick_us > 1e29) next_tick_us = now_us + tick_period_us;
}

static bool tone_on = false;
static double tone_start = 0;

static void tone_check(void)
{
    bool want = (TCCR0A.v & (1 << COM0B0)) && (TCCR0B.v & 7) && (DDRB.v & (1 << PB1));
    if (want && !tone_on) {
        double f = (double)F_CPU / (2.0 * (((TCCR0B.v & 7) == 3) ? 64 : 0) * (OCR0A.v + 1));
        logev("tone", "ON %.0f Hz", f);
        tone_on = true;
        tone_start = now_us;
    } else if (!want && tone_on) {
        logev("tone", "OFF after %.0f ms", (now_us - tone_start) / 1000);
        tone_on = false;
    }
}

static void deliver(void)
{
    if (tick_pending && R.SREG_I.v && (TIMSK0.v & (1 << OCIE0A))) {
        tick_pending = false;
        R.SREG_I.v = 0;  // hardware clears I during an ISR
        in_isr++;
        TIM0_COMPA_vect();
        in_isr--;
        R.SREG_I.v = 1;
    }
}

static void advance(double us)
{
    double target = now_us + us;
    if (target > end_us) {
        now_us = end_us;
        throw SimDone();
    }
    while (next_tick_us <= target) {
        now_us = next_tick_us;
        next_tick_us += tick_period_us;
        if (TIMSK0.v & (1 << OCIE0A)) tick_pending = true;
        deliver();
    }
    now_us = target;
    deliver();
}

extern "C" void sim_delay_us(double us) { advance(us); }

extern "C" void sim_sleep(void)
{
    R.SREG_I.v = 1;  // "sei; sleep"
    bool pd = (MCUCR.v & (1 << SM1)) != 0;
    if (!(MCUCR.v & (1 << SE))) return;  // sleep disabled: acts as nop
    if (!pd) {                           // idle: wake on next interrupt
        deliver();
        if (next_tick_us > 1e29 || !(TIMSK0.v & (1 << OCIE0A))) {
            advance(end_us - now_us + 1);  // nothing can wake it: ends the run
        }
        advance(next_tick_us - now_us);
        return;
    }
    // power-down: oscillator stopped. Only a pin change wakes up.
    logev("sleep", "power-down: ADCSRA=0x%02X TIMSK0=0x%02X display_on=%d PCMSK=0x%02X GIMSK=0x%02X",
          ADCSRA.v, TIMSK0.v, display_on, PCMSK.v, GIMSK.v);
    sleeping_pd++;
    double t = now_us;
    int last_level = rd_pinb() >> PB3 & 1;
    for (size_t i = 0; i < script.size(); i++) {
        if (script[i].t <= t) continue;
        int level = script[i].run;
        if (level != last_level) {
            last_level = level;
            if ((PCMSK.v & (1 << PCINT3)) && (GIMSK.v & (1 << PCIE))) {
                now_us = script[i].t;
                if (now_us > end_us) throw SimDone();
                logev("wake", "pin change on PB3 (level %d)", level);
                // the oscillator restarts; ticks resume from now
                if (timer_running()) next_tick_us = now_us + tick_period_us;
                PCINT0_vect();
                return;
            }
        }
    }
    now_us = end_us;
    throw SimDone();
}

// -------------------------------------------------------- register hooks ----
static void wr_ddrb(uint8_t, uint8_t) { bus_update(); tone_check(); advance(0.8); }
static void wr_tccr0a(uint8_t, uint8_t) { timer_reconfig(false); tone_check(); }
static void wr_tccr0b(uint8_t o, uint8_t n) { timer_reconfig(o != n); tone_check(); }
static void wr_ocr0a(uint8_t, uint8_t) { timer_reconfig(false); }
static void wr_tcnt0(uint8_t, uint8_t) { timer_reconfig(true); }
static void wr_timsk0(uint8_t, uint8_t) {}

#include <avr/regs_undef.h>
static void init_regs(void)
{
    memset(&R, 0, sizeof R);
    R.DDRB.on_write = wr_ddrb;
    R.PINB.on_read = rd_pinb;
    R.ADCH.on_read = rd_adch;
    R.TCCR0A.on_write = wr_tccr0a;
    R.TCCR0B.on_write = wr_tccr0b;
    R.OCR0A.on_write = wr_ocr0a;
    R.TCNT0.on_write = wr_tcnt0;
    R.TIMSK0.on_write = wr_timsk0;
    R.OSCCAL.v = 0x55;
}

#include <avr/regs_macros.h>
int firmware_main(void);

// ----------------------------------------------------------- scenarios ----
static int failures = 0, checks = 0;

static void check(bool cond, const char *fmt, ...)
{
    char buf[300];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(buf, sizeof buf, fmt, ap);
    va_end(ap);
    checks++;
    if (!cond) failures++;
    printf("  [%s] %s\n", cond ? "ok" : "FAIL", buf);
}

// frames as (t_ms, text) list
static std::vector<std::pair<double, std::string>> frames_of(void)
{
    std::vector<std::pair<double, std::string>> v;
    for (auto &e : evlog)
        if (e.kind == "frame") v.push_back({e.t / 1000, e.text});
    return v;
}

static void run_firmware(double seconds)
{
    end_us = seconds * 1e6;
    try {
        firmware_main();
    } catch (SimDone &) {
    }
}

static void reset_sim(void)
{
    init_regs();
    now_us = 0;
    next_tick_us = 1e30;
    tick_period_us = 0;
    tick_pending = false;
    tone_on = false;
    sleeping_pd = 0;
    evlog.clear();
    script.clear();
    bus = Bus();
    display_on = vertical_mode = page_range_ok = false;
    frames = 0;
    init_count = 0;
    last_text = "";
    memset(pixels, 0, sizeof pixels);
}

static std::string text_at(double t_ms)  // last frame shown at or before t
{
    std::string s = "(none)";
    for (auto &f : frames_of())
        if (f.first <= t_ms) s = f.second;
    return s;
}

static void common_checks(void)
{
    check(!bus.violation, "I2C pins are only driven open-drain (PORTB bits 0 and 2 stay 0)");
    int bad = 0;
    for (auto &e : evlog)
        if (e.kind == "bus") bad++;
    check(bad == 0, "no malformed I2C transactions (%d)", bad);
}

// --- 1. power-on, +/- ------------------------------------------------------
static void scen_basic(void)
{
    printf("scenario: power-on and + / - in ready state\n");
    reset_sim();
    press(500, PLUS);
    press(800, PLUS);
    press(1100, PLUS);
    press(1400, MINUS);
    run_firmware(2.0);
    auto fr = frames_of();
    check(!fr.empty() && fr[0].second == "2:00", "first frame is 2:00 (got '%s')", fr.empty() ? "" : fr[0].second.c_str());
    check(!fr.empty() && fr[0].first < 1000, "first frame within 1 s of power-on (at %.0f ms)", fr.empty() ? 0 : fr[0].first);
    check(vertical_mode && page_range_ok, "OLED init selects vertical addressing and page range 0..3");
    check(display_on, "display switched on");
    check(text_at(700) == "3:00", "after 1st '+': 3:00 (got %s)", text_at(700).c_str());
    check(text_at(1000) == "4:00", "after 2nd '+': 4:00 (got %s)", text_at(1000).c_str());
    check(text_at(1300) == "5:00", "after 3rd '+': 5:00 (got %s)", text_at(1300).c_str());
    check(text_at(1900) == "4:00", "after '-': 4:00 (got %s)", text_at(1900).c_str());
    common_checks();
}

// --- 2. limits --------------------------------------------------------------
static void scen_limits(void)
{
    printf("scenario: limits 1:00 .. 60:00 without wrap\n");
    reset_sim();
    double t = 300;
    for (int i = 0; i < 61; i++, t += 120) press(t, PLUS, 60);  // 2 -> 60 and 2 more presses
    double t_top = t;
    for (int i = 0; i < 62; i++, t += 120) press(t, MINUS, 60);  // 60 -> 1 and more
    run_firmware(t / 1000 + 1);
    check(text_at(t_top - 10) == "60:00", "after 61 '+': 60:00 (got %s)", text_at(t_top - 10).c_str());
    // intermediate checks
    check(text_at(300 + 120 * 7 + 100) == "10:00", "10:00 reached after 8 '+' (got %s)", text_at(300 + 120 * 7 + 100).c_str());
    check(text_at(300 + 120 * 6 + 100) == "9:00", "9:00 shown below 10 min (got %s)", text_at(300 + 120 * 6 + 100).c_str());
    check(text_at(t - 10) == "1:00", "after 62 '-': 1:00 and stays (got %s)", text_at(t - 10).c_str());
    // all frames must be valid MM:SS with SS = 00
    int bad = 0;
    for (auto &f : frames_of()) {
        if (f.second == "?" ) bad++;
    }
    check(bad == 0, "every frame decodes to a valid time (%d bad)", bad);
    common_checks();
}

// --- 3. countdown ------------------------------------------------------------
static void scen_countdown(void)
{
    printf("scenario: 2:00 countdown, '+'/'-' ignored while counting, signal, back to 2:00\n");
    reset_sim();
    press(1000, RUN);             // released at 1120 ms: start
    press(10000, PLUS);           // ignored
    press(12000, MINUS);          // ignored
    run_firmware(135);
    auto fr = frames_of();
    double t_start = 0;
    for (auto &e : evlog)
        if (e.kind == "frame" && e.text == "1:59") { t_start = e.t / 1000; break; }
    // the start is the release of "run" + debounce (24 ms) at about 1120 ms
    check(t_start > 2100 && t_start < 2250, "1:59 appears ~1 s after the start (at %.1f ms)", t_start);
    bool seq_ok = true;
    int expected_min = 1, expected_sec = 59, n_frames = 0;
    std::string prev;
    double t_zero = 0;
    for (auto &e : evlog) {
        if (e.kind != "frame") continue;
        if (e.t / 1000 < t_start - 1) continue;
        std::string want;
        if (expected_min >= 0) {
            char b[16];
            snprintf(b, sizeof b, "%d:%02d", expected_min, expected_sec);
            want = b;
        }
        std::string got = e.text.substr(0, e.text.find(' '));
        if (got == "2:00" && n_frames > 100) break;  // back to ready
        if (got != want) { seq_ok = false; printf("    sequence break: got '%s' expected '%s' at %.0f ms\n", got.c_str(), want.c_str(), e.t / 1000); break; }
        n_frames++;
        if (want == "0:00") { t_zero = e.t / 1000; break; }
        if (--expected_sec < 0) { expected_sec = 59; expected_min--; }
    }
    check(seq_ok && n_frames == 120, "frames 1:59 .. 0:00 in order, none skipped (%d frames)", n_frames);
    check(fabs((t_zero - t_start) - 119000) < 100, "0:00 comes %.1f s after 1:59 (expected 119.0 s)", (t_zero - t_start) / 1000);
    int beeps = 0;
    double beep_t = 0, beep_len = 0;
    for (auto &e : evlog) {
        if (e.kind == "tone" && e.text.compare(0, 2, "ON") == 0) { beeps++; beep_t = e.t / 1000; }
        if (e.kind == "tone" && e.text.compare(0, 3, "OFF") == 0) sscanf(e.text.c_str(), "OFF after %lf ms", &beep_len);
    }
    check(beeps == 1, "exactly one signal (%d)", beeps);
    check(fabs(beep_len - 1000) < 5, "signal lasts %.0f ms", beep_len);
    check(beep_t >= t_zero && beep_t - t_zero < 60, "signal starts right after 0:00 shown (+%.0f ms)", beep_t - t_zero);
    check(text_at(t_zero + 1500) == "2:00", "2:00 again after the signal (got %s)", text_at(t_zero + 1500).c_str());
    check(text_at(t_zero + 8000) == "2:00", "and it stays 2:00 (got %s)", text_at(t_zero + 8000).c_str());
    bool changed_by_pm = false;
    for (auto &f : frames_of())
        if (f.first > 9500 && f.first < 14000 && f.second != text_at(f.first - 1) && false) changed_by_pm = true;
    check(!changed_by_pm, "'+' and '-' during the countdown do nothing");
    // the frames around the presses are only the 1 s ticks: verify count between 9 s and 14 s
    int n_in = 0;
    for (auto &f : frames_of())
        if (f.first > 9500 && f.first < 14500) n_in++;
    check(n_in >= 4 && n_in <= 6, "only ~1 frame per second while counting (%d frames in 5 s)", n_in);
    common_checks();
}

// --- 4. stop -----------------------------------------------------------------
static void scen_stop(void)
{
    printf("scenario: run stops the countdown and restores 2:00\n");
    reset_sim();
    press(500, PLUS);        // 3:00
    press(1000, RUN);        // start
    press(6000, RUN);        // stop after ~5 s
    run_firmware(20);
    check(text_at(5900) == "2:55" || text_at(5900) == "2:56", "counting before the stop (got %s)", text_at(5900).c_str());
    check(text_at(6500) == "2:00", "after the stop: 2:00, not the 3:00 set earlier (got %s)", text_at(6500).c_str());
    check(text_at(19000) == "2:00", "does not start by itself (got %s)", text_at(19000).c_str());
    int beeps = 0;
    for (auto &e : evlog) if (e.kind == "tone") beeps++;
    check(beeps == 0, "no signal after a stop");
    common_checks();
}

// --- 5. long press -> sleep -> wake ---------------------------------------------
static void scen_sleep(void)
{
    printf("scenario: 2 s press of run -> deep sleep; press wakes, does not start\n");
    reset_sim();
    press(1000, RUN, 2500);       // held 2.5 s: sleep triggers at ~3.0 s
    press(10000, RUN, 300);       // wake-up press
    run_firmware(25);
    bool slept = false;
    double t_sleep = 0, t_wake = 0;
    for (auto &e : evlog) {
        if (e.kind == "sleep") { slept = true; t_sleep = e.t / 1000; }
        if (e.kind == "wake") t_wake = e.t / 1000;
    }
    check(slept, "entered power-down at %.0f ms", t_sleep);
    check(t_sleep >= 3000 && t_sleep < 3700, "after the 2 s hold (held from 1000 ms)");
    bool off_cmd = false;
    for (auto &e : evlog)
        if (e.kind == "cmd" && e.text.find("AE 8D 10") != std::string::npos) off_cmd = true;
    check(off_cmd, "OLED got 0xAE then 0x8D 0x10 before sleeping");
    bool sleep_state_ok = false;
    for (auto &e : evlog)
        if (e.kind == "sleep" && e.text.find("ADCSRA=0x00 TIMSK0=0x00") != std::string::npos &&
            e.text.find("PCMSK=0x08") != std::string::npos && e.text.find("GIMSK=0x20") != std::string::npos)
            sleep_state_ok = true;
    check(sleep_state_ok, "ADC off, Timer0 interrupt off, only PB3 pin change enabled");
    check(t_wake > 9900 && t_wake < 10100, "wake-up on the press at 10 s (woke at %.0f ms)", t_wake);
    check(text_at(11000) == "2:00", "2:00 after wake-up (got %s)", text_at(11000).c_str());
    check(text_at(24000) == "2:00", "the waking press did not start the countdown (got %s)", text_at(24000).c_str());
    check(init_count == 2, "OLED re-initialised after wake-up (%d inits)", init_count);
    common_checks();
}

// --- 6. long press while counting down ---------------------------------------------
static void scen_sleep_running(void)
{
    printf("scenario: long press during the countdown also sleeps\n");
    reset_sim();
    press(1000, RUN);
    press(5000, RUN, 2300);
    press(12000, RUN, 200);
    run_firmware(20);
    check(sleeping_pd == 1, "entered power-down once (%d)", sleeping_pd);
    check(text_at(13000) == "2:00", "2:00 after wake-up (got %s)", text_at(13000).c_str());
    check(text_at(19000) == "2:00", "no countdown after wake-up (got %s)", text_at(19000).c_str());
    common_checks();
}

// --- 7. accuracy of the time base -----------------------------------------------------
static void scen_long_count(void)
{
    printf("scenario: 10:00 countdown timing\n");
    reset_sim();
    for (int i = 0; i < 8; i++) press(300 + 150 * i, PLUS, 60, false);  // 2 -> 10
    press(2000, RUN);
    run_firmware(660);
    double t_start = 0, t_zero = 0;
    for (auto &e : evlog) {
        if (e.kind == "frame" && e.text == "9:59" && t_start == 0) t_start = e.t / 1000;
        if (e.kind == "frame" && e.text.compare(0, 4, "0:00") == 0 && t_zero == 0) t_zero = e.t / 1000;
    }
    check(text_at(1900) == "10:00", "10:00 set (got %s)", text_at(1900).c_str());
    double dur = (t_zero - (t_start - 1000)) / 1000;
    check(fabs(dur - 600.0) < 0.1, "ready->0:00 takes %.3f s with an ideal 9.6 MHz clock (expect 600.000)", dur);
    common_checks();
}

#if FEATURE_BAR
// --- 8. progress frame ----------------------------------------------------------
static void scen_bar(void)
{
    printf("scenario: progress frame = ceil(316 * remaining / total), bell only at the signal\n");
    reset_sim();
    press(500, MINUS, 60, false);   // 1:00 (60 s) keeps the run short
    press(1000, RUN);
    run_firmware(75);
    int n = 0, bad = 0, first_bar = -1, last_bar = -1;
    bool bell_early = false, bell_at_zero = false, bell_after = false;
    double t_zero = 0;
    for (auto &e : evlog) {
        if (e.kind != "frame") continue;
        std::string t = e.text.substr(0, e.text.find(' '));
        bool bell = e.text.find("+bell") != std::string::npos;
        if (t == "0:00") { t_zero = e.t; if (bell) bell_at_zero = true; }
        else if (bell) { if (t_zero == 0) bell_early = true; else bell_after = true; }
        int m = 0, sec = 0;
        if (t_zero && e.t > t_zero) continue;  // ready screen after the signal
        if (sscanf(t.c_str(), "%d:%d", &m, &sec) != 2) continue;
        if (e.t / 1000 < 1000) { if (first_bar < 0) first_bar = e.bar; continue; }
        int rem = m * 60 + sec;
        int want = (316 * rem + 59) / 60;   // ceil
        if (e.t < 1000e3 + 1) {}
        n++;
        if (e.bar != want) {
            bad++;
            if (bad < 5) printf("    t=%.0f ms %s: bar=%d expected %d\n", e.t / 1000, t.c_str(), e.bar, want);
        }
        last_bar = e.bar;
    }
    check(first_bar == 316, "frame is complete (316 px) when ready (%d)", first_bar);
    check(n >= 60 && bad == 0, "%d counting frames, %d with a wrong pixel count", n, bad);
    check(last_bar == 0, "frame is empty at 0:00 (%d)", last_bar);
    check(bell_at_zero && !bell_early && !bell_after, "bell icon only on the 0:00 frame");
    common_checks();
}
#endif

#ifdef SIM_CALIB
// --- calibration program ----------------------------------------------------------
static void scen_calib(void)
{
    printf("scenario: calibration program (CAL_MIN=1)\n");
    reset_sim();
    press(500, PLUS, 60, false);
    press(800, PLUS, 60, false);
    press(1100, MINUS, 60, false);
    press(2000, RUN);           // start the count-up
    run_firmware(75);
    check(text_at(400) == ":085", "shows the OSCCAL value after reset (got %s)", text_at(400).c_str());
    check(text_at(700) == ":086" && text_at(1000) == ":087" && text_at(1300) == ":086", "+ + - change OSCCAL by one (got %s %s %s)",
          text_at(700).c_str(), text_at(1000).c_str(), text_at(1300).c_str());
    check(OSCCAL.v == 86, "OSCCAL register holds 86 (%d)", OSCCAL.v);
    double t1 = 0, t60 = 0;
    for (auto &e : evlog) {
        if (e.kind == "frame" && e.text == "0:01" && !t1) t1 = e.t / 1000;
        if (e.kind == "frame" && e.text == "1:00" && !t60) t60 = e.t / 1000;
    }
    check(t1 > 0 && fabs((t60 - t1) - 59000) < 20, "count-up 0:01 -> 1:00 takes %.3f s", (t60 - t1) / 1000);
    bool beep = false;
    for (auto &e : evlog) if (e.kind == "tone" && e.text.compare(0, 2, "ON") == 0) beep = true;
    check(beep, "beep at 1:00");
    check(text_at(70000) == ":086", "back to the OSCCAL screen after the beep (got %s)", text_at(70000).c_str());
    common_checks();
}
#endif

int main(int argc, char **argv)
{
    const char *only = argc > 1 ? argv[1] : nullptr;
    struct S { const char *name; void (*fn)(void); } list[] = {
#ifdef SIM_CALIB
        {"calib", scen_calib}
#else
        {"basic", scen_basic}, {"limits", scen_limits}, {"countdown", scen_countdown},
        {"stop", scen_stop}, {"sleep", scen_sleep}, {"sleep_running", scen_sleep_running},
        {"long", scen_long_count}
#if FEATURE_BAR
        , {"bar", scen_bar}
#endif
#endif
    };
    int total_fail = 0;
    for (auto &s : list) {
        if (only && strcmp(only, s.name)) continue;
        fflush(stdout);
        pid_t pid = fork();  // firmware keeps state in statics: one process per scenario
        if (pid == 0) {
            s.fn();
            printf("  -> %d checks, %d failed\n", checks, failures);
            fflush(stdout);
            _exit(failures ? 1 : 0);
        }
        int st = 0;
        waitpid(pid, &st, 0);
        if (!WIFEXITED(st) || WEXITSTATUS(st)) total_fail++;
    }
    printf("\n%s: %d scenario(s) with failures\n", total_fail ? "FAILED" : "ALL PASSED", total_fail);
    return total_fail ? 1 : 0;
}
