/* Host test for firmware/src/render.c: renders a frame into a 128x32 pixel
 * array (decoding the same byte stream the OLED receives in vertical
 * addressing mode) and prints it as ASCII art / PGM.
 *
 *   cc -DFEATURE_BAR=1 -DFEATURE_BELL=1 -Ifirmware/src -o host_render \
 *      tools/host_render.c firmware/src/render.c && ./host_render 0 2 0 0
 *
 * Arguments: m10 m1 s10 s1 [bar_lit] [bell]  (digits of the time)          */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "oled.h"

static uint8_t stream[512];
static int n;

void oled_put(uint8_t b)
{
    if (n < 512)
        stream[n] = b;
    n++;
}

int main(int argc, char **argv)
{
    if (argc < 5) {
        fprintf(stderr, "usage: %s m10 m1 s10 s1 [bar_lit [bell]]\n", argv[0]);
        return 2;
    }
    for (int i = 0; i < 5; i++)
        txt[i] = 0;
    txt[0] = atoi(argv[1]);
    txt[1] = atoi(argv[2]);
    txt[2] = GLYPH_COLON;
    txt[3] = atoi(argv[3]);
    txt[4] = atoi(argv[4]);
#if FEATURE_BAR
    bar_lit = argc > 5 ? atoi(argv[5]) : BAR_PIXELS;
#endif
#if FEATURE_BELL
    bell = argc > 6 ? atoi(argv[6]) : 0;
#endif
    render_frame();
    if (n != 512) {
        fprintf(stderr, "ERROR: frame has %d bytes, expected 512\n", n);
        return 1;
    }
    static uint8_t px[32][128];
    int lit = 0;
    for (int x = 0; x < 128; x++)
        for (int page = 0; page < 4; page++)
            for (int bit = 0; bit < 8; bit++)
                if ((stream[x * 4 + page] >> bit) & 1) {
                    px[page * 8 + bit][x] = 1;
                    lit++;
                }
    if (getenv("PGM")) {
        printf("P1\n128 32\n");
        for (int y = 0; y < 32; y++) {
            for (int x = 0; x < 128; x++)
                putchar(px[y][x] ? '1' : '0');
            putchar('\n');
        }
        return 0;
    }
    for (int y = 0; y < 32; y++) {
        for (int x = 0; x < 128; x++)
            putchar(px[y][x] ? '#' : '.');
        putchar('\n');
    }
    printf("lit pixels: %d\n", lit);
    return 0;
}
