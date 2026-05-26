#include "timing.h"

#include <time.h>

static int g_utc_offset_ready = 0;
static uint64_t g_utc_offset_us = 0;

uint64_t wb_monotonic_us(void)
{
	struct timespec ts;
	clock_gettime(CLOCK_MONOTONIC, &ts);
	return (uint64_t)ts.tv_sec * 1000000ULL + (uint64_t)(ts.tv_nsec / 1000);
}

uint64_t wb_utc_offset_us(void)
{
	if (!g_utc_offset_ready) {
		struct timespec rt, mono;
		clock_gettime(CLOCK_REALTIME, &rt);
		clock_gettime(CLOCK_MONOTONIC, &mono);
		uint64_t rt_us = (uint64_t)rt.tv_sec * 1000000ULL +
			(uint64_t)(rt.tv_nsec / 1000);
		uint64_t mono_us = (uint64_t)mono.tv_sec * 1000000ULL +
			(uint64_t)(mono.tv_nsec / 1000);
		g_utc_offset_us = rt_us - mono_us;
		g_utc_offset_ready = 1;
	}
	return g_utc_offset_us;
}

uint64_t wb_monotonic_to_utc_us(uint64_t mono_us)
{
	return mono_us + wb_utc_offset_us();
}
