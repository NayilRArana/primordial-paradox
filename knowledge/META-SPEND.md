# Meta spend, measured (card t_5031b766)

Every live Meta Model API call recorded in `data/ai_cache`, priced at the documented list price. This page is generated from the cache by `tools/meta_spend_ledger.py`; a replayed or mock answer is not in it, because it cost nothing and crossed no network.

Generated 2026-10-27 10:13 UTC from 274 live cache entries (2026-10-27T00:02:47Z to 2026-10-27T10:00:27Z). The cache also holds 11 mock entries, which are not counted.

## 1. Prices used, and where they come from

`arananet/meta-hackathon/HACKATHON-BRIEF.md` section 3.2, read 2026-10-21 from https://dev.meta.ai/docs/pricing-rate-limits and repeated on the model pages:

| model | unit | price |
| --- | --- | --- |
| muse-spark-1.3 | fresh input tokens | 1.25 USD per 1M |
| muse-spark-1.3 | cached input tokens | 0.15 USD per 1M |
| muse-spark-1.3 | output tokens | 4.25 USD per 1M |
| muse-image-1.0 | generated or edited image | 0.01 USD per image, flat |
| sam-3.1 | image segmentation | 2.50 USD per 1,000 images (0.0025 each) |

The token counts are the API's own `usage` object as it was stored with each answer, so the arithmetic below is over measured tokens, not an estimate from character counts. The reasoning tokens Muse Spark reports are already inside `completion_tokens` and are billed at the output rate.

## 2. The total

| window | live calls | cost, USD |
| --- | --- | --- |
| A: live work recorded before this worker's first command (2026-10-27T00:02:47Z to just before 2026-10-27T01:43:26Z) | 118 | 1.3243 |
| B: everything recorded from 2026-10-27T01:43:26Z to now | 156 | 1.8825 |
| **all live calls in the cache** | **274** | **3.2068** |

A cache entry records the model, the request and the answer, and not which process or lane asked for it, so window B is a time window and not an attribution: it holds this worker's own calls and any other run that was live in the same minutes. The number that is exact is the total.

The card's ceiling is 40.00 USD of measured spend. Measured: **3.2068 USD**, which is 8.02 percent of the ceiling. The cost inside window B (this worker's own calls plus any other live run in the same minutes) is 1.8825 USD.

## 3. By kind and model

| window | kind | model | calls | fresh in | cached in | out | images | cost, USD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | chat | muse-spark-1.3 | 111 | 49809 | 78130 | 260606 | 0 | 1.1816 |
| A | segment | sam-3.1 | 2 | 0 | 0 | 0 | 0 | 0.0050 |
| A | vision | muse-spark-1.3 | 5 | 10670 | 0 | 29272 | 0 | 0.1377 |
| B | chat | muse-spark-1.3 | 139 | 113688 | 35820 | 333699 | 0 | 1.5657 |
| B | edit | muse-image-1.0 | 1 | 0 | 0 | 0 | 1 | 0.0100 |
| B | image | muse-image-1.0 | 2 | 0 | 0 | 0 | 2 | 0.0200 |
| B | segment | sam-3.1 | 2 | 0 | 0 | 0 | 0 | 0.0050 |
| B | vision | muse-spark-1.3 | 12 | 20962 | 867 | 60116 | 0 | 0.2818 |

Live calls per kind, the number the card asks the cache to show is greater than zero for: chat 250, edit 1, image 2, segment 4, vision 17.

## 4. Every live call, in the order it was made

| recorded_at | kind | model | fresh in | cached in | out | USD |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-10-27T00:02:47Z | chat | muse-spark-1.3 | 15 | 0 | 1043 | 0.00445 |
| 2026-10-27T00:11:53Z | chat | muse-spark-1.3 | 1057 | 0 | 1359 | 0.00710 |
| 2026-10-27T00:12:03Z | chat | muse-spark-1.3 | 1056 | 0 | 2314 | 0.01115 |
| 2026-10-27T00:12:15Z | chat | muse-spark-1.3 | 1052 | 0 | 1595 | 0.00809 |
| 2026-10-27T00:12:23Z | chat | muse-spark-1.3 | 1051 | 0 | 2273 | 0.01097 |
| 2026-10-27T00:12:35Z | chat | muse-spark-1.3 | 1073 | 0 | 1628 | 0.00826 |
| 2026-10-27T00:12:43Z | chat | muse-spark-1.3 | 1078 | 0 | 1904 | 0.00944 |
| 2026-10-27T00:13:02Z | chat | muse-spark-1.3 | 1090 | 0 | 2396 | 0.01155 |
| 2026-10-27T00:13:14Z | chat | muse-spark-1.3 | 1092 | 0 | 3048 | 0.01432 |
| 2026-10-27T00:13:43Z | chat | muse-spark-1.3 | 344 | 753 | 4357 | 0.01906 |
| 2026-10-27T00:13:56Z | chat | muse-spark-1.3 | 1099 | 0 | 3288 | 0.01535 |
| 2026-10-27T00:14:16Z | chat | muse-spark-1.3 | 347 | 753 | 2192 | 0.00986 |
| 2026-10-27T00:14:29Z | chat | muse-spark-1.3 | 1102 | 0 | 3260 | 0.01523 |
| 2026-10-27T00:19:07Z | chat | muse-spark-1.3 | 1067 | 0 | 1720 | 0.00864 |
| 2026-10-27T00:19:13Z | chat | muse-spark-1.3 | 1063 | 0 | 1759 | 0.00880 |
| 2026-10-27T00:19:32Z | chat | muse-spark-1.3 | 307 | 753 | 2206 | 0.00987 |
| 2026-10-27T00:19:41Z | chat | muse-spark-1.3 | 1058 | 0 | 1696 | 0.00853 |
| 2026-10-27T00:19:58Z | chat | muse-spark-1.3 | 1076 | 0 | 2065 | 0.01012 |
| 2026-10-27T00:20:06Z | chat | muse-spark-1.3 | 1074 | 0 | 1963 | 0.00969 |
| 2026-10-27T00:20:25Z | chat | muse-spark-1.3 | 1091 | 0 | 1869 | 0.00931 |
| 2026-10-27T00:20:38Z | chat | muse-spark-1.3 | 1097 | 0 | 2842 | 0.01345 |
| 2026-10-27T00:21:16Z | chat | muse-spark-1.3 | 1100 | 0 | 6013 | 0.02693 |
| 2026-10-27T00:21:27Z | chat | muse-spark-1.3 | 351 | 753 | 2280 | 0.01024 |
| 2026-10-27T00:22:07Z | chat | muse-spark-1.3 | 346 | 753 | 3525 | 0.01553 |
| 2026-10-27T00:29:53Z | chat | muse-spark-1.3 | 1063 | 0 | 2292 | 0.01107 |
| 2026-10-27T00:29:57Z | chat | muse-spark-1.3 | 1061 | 0 | 1345 | 0.00704 |
| 2026-10-27T00:30:06Z | chat | muse-spark-1.3 | 182 | 881 | 1162 | 0.00530 |
| 2026-10-27T00:30:12Z | chat | muse-spark-1.3 | 309 | 753 | 1287 | 0.00597 |
| 2026-10-27T00:30:23Z | chat | muse-spark-1.3 | 58 | 1009 | 2892 | 0.01251 |
| 2026-10-27T00:30:30Z | chat | muse-spark-1.3 | 322 | 753 | 1915 | 0.00865 |
| 2026-10-27T00:30:36Z | chat | muse-spark-1.3 | 323 | 753 | 1623 | 0.00741 |
| 2026-10-27T00:31:01Z | chat | muse-spark-1.3 | 338 | 753 | 2606 | 0.01161 |
| 2026-10-27T00:31:25Z | chat | muse-spark-1.3 | 87 | 1009 | 5102 | 0.02194 |
| 2026-10-27T00:31:51Z | chat | muse-spark-1.3 | 1099 | 0 | 3514 | 0.01631 |
| 2026-10-27T00:32:06Z | chat | muse-spark-1.3 | 1100 | 0 | 3473 | 0.01614 |
| 2026-10-27T00:32:24Z | chat | muse-spark-1.3 | 344 | 753 | 1869 | 0.00849 |
| 2026-10-27T00:32:34Z | chat | muse-spark-1.3 | 340 | 753 | 2285 | 0.01025 |
| 2026-10-27T00:34:49Z | vision | muse-spark-1.3 | 6253 | 0 | 7549 | 0.03990 |
| 2026-10-27T00:42:06Z | vision | muse-spark-1.3 | 1103 | 0 | 6060 | 0.02713 |
| 2026-10-27T00:42:35Z | vision | muse-spark-1.3 | 1105 | 0 | 6030 | 0.02701 |
| 2026-10-27T00:42:59Z | vision | muse-spark-1.3 | 1105 | 0 | 5995 | 0.02686 |
| 2026-10-27T00:43:13Z | vision | muse-spark-1.3 | 1104 | 0 | 3638 | 0.01684 |
| 2026-10-27T00:50:58Z | segment | sam-3.1 | 0 | 0 | 0 | 0.00250 |
| 2026-10-27T00:53:43Z | chat | muse-spark-1.3 | 65 | 1137 | 2604 | 0.01132 |
| 2026-10-27T00:53:49Z | chat | muse-spark-1.3 | 451 | 753 | 1897 | 0.00874 |
| 2026-10-27T00:53:59Z | chat | muse-spark-1.3 | 66 | 1137 | 2889 | 0.01253 |
| 2026-10-27T00:54:08Z | chat | muse-spark-1.3 | 451 | 753 | 2617 | 0.01180 |
| 2026-10-27T00:54:17Z | chat | muse-spark-1.3 | 66 | 1137 | 2643 | 0.01149 |
| 2026-10-27T00:54:24Z | chat | muse-spark-1.3 | 66 | 1137 | 2298 | 0.01002 |
| 2026-10-27T00:54:31Z | chat | muse-spark-1.3 | 65 | 1137 | 2457 | 0.01069 |
| 2026-10-27T00:54:39Z | chat | muse-spark-1.3 | 67 | 1137 | 2264 | 0.00988 |
| 2026-10-27T00:54:49Z | chat | muse-spark-1.3 | 450 | 753 | 2988 | 0.01337 |
| 2026-10-27T00:54:55Z | chat | muse-spark-1.3 | 64 | 1137 | 2112 | 0.00923 |
| 2026-10-27T00:55:03Z | chat | muse-spark-1.3 | 449 | 753 | 2355 | 0.01068 |
| 2026-10-27T00:55:11Z | chat | muse-spark-1.3 | 66 | 1137 | 2535 | 0.01103 |
| 2026-10-27T00:55:18Z | chat | muse-spark-1.3 | 67 | 1137 | 1948 | 0.00853 |
| 2026-10-27T00:55:28Z | chat | muse-spark-1.3 | 448 | 753 | 3208 | 0.01431 |
| 2026-10-27T00:55:34Z | chat | muse-spark-1.3 | 70 | 1137 | 1626 | 0.00717 |
| 2026-10-27T00:55:48Z | chat | muse-spark-1.3 | 65 | 1137 | 1939 | 0.00849 |
| 2026-10-27T00:55:54Z | chat | muse-spark-1.3 | 446 | 753 | 1712 | 0.00795 |
| 2026-10-27T00:56:00Z | chat | muse-spark-1.3 | 66 | 1137 | 2211 | 0.00965 |
| 2026-10-27T00:56:06Z | chat | muse-spark-1.3 | 63 | 1137 | 1730 | 0.00760 |
| 2026-10-27T00:56:11Z | chat | muse-spark-1.3 | 451 | 753 | 1461 | 0.00689 |
| 2026-10-27T00:56:19Z | chat | muse-spark-1.3 | 65 | 1137 | 2765 | 0.01200 |
| 2026-10-27T00:56:25Z | chat | muse-spark-1.3 | 64 | 1137 | 1815 | 0.00796 |
| 2026-10-27T00:56:29Z | chat | muse-spark-1.3 | 64 | 1137 | 1101 | 0.00493 |
| 2026-10-27T00:56:33Z | chat | muse-spark-1.3 | 63 | 1137 | 1487 | 0.00657 |
| 2026-10-27T00:56:40Z | chat | muse-spark-1.3 | 64 | 1137 | 2245 | 0.00979 |
| 2026-10-27T00:56:44Z | chat | muse-spark-1.3 | 64 | 1137 | 1236 | 0.00550 |
| 2026-10-27T00:56:51Z | chat | muse-spark-1.3 | 63 | 1137 | 2060 | 0.00900 |
| 2026-10-27T00:56:57Z | chat | muse-spark-1.3 | 64 | 1137 | 1842 | 0.00808 |
| 2026-10-27T00:57:03Z | chat | muse-spark-1.3 | 63 | 1137 | 2145 | 0.00937 |
| 2026-10-27T00:59:26Z | segment | sam-3.1 | 0 | 0 | 0 | 0.00250 |
| 2026-10-27T00:59:56Z | chat | muse-spark-1.3 | 66 | 1137 | 2038 | 0.00891 |
| 2026-10-27T01:06:21Z | chat | muse-spark-1.3 | 71 | 1137 | 4163 | 0.01795 |
| 2026-10-27T01:06:29Z | chat | muse-spark-1.3 | 69 | 1137 | 2639 | 0.01147 |
| 2026-10-27T01:06:37Z | chat | muse-spark-1.3 | 70 | 1137 | 2452 | 0.01068 |
| 2026-10-27T01:06:47Z | chat | muse-spark-1.3 | 69 | 1137 | 3399 | 0.01470 |
| 2026-10-27T01:06:56Z | chat | muse-spark-1.3 | 71 | 1137 | 3106 | 0.01346 |
| 2026-10-27T01:07:04Z | chat | muse-spark-1.3 | 71 | 1137 | 2643 | 0.01149 |
| 2026-10-27T01:07:11Z | chat | muse-spark-1.3 | 69 | 1137 | 2547 | 0.01108 |
| 2026-10-27T01:07:19Z | chat | muse-spark-1.3 | 69 | 1137 | 2369 | 0.01033 |
| 2026-10-27T01:07:31Z | chat | muse-spark-1.3 | 68 | 1137 | 3554 | 0.01536 |
| 2026-10-27T01:07:37Z | chat | muse-spark-1.3 | 72 | 1137 | 1856 | 0.00815 |
| 2026-10-27T01:07:46Z | chat | muse-spark-1.3 | 69 | 1137 | 2897 | 0.01257 |
| 2026-10-27T01:07:55Z | chat | muse-spark-1.3 | 1206 | 0 | 2929 | 0.01396 |
| 2026-10-27T01:08:03Z | chat | muse-spark-1.3 | 452 | 753 | 2476 | 0.01120 |
| 2026-10-27T01:08:14Z | chat | muse-spark-1.3 | 69 | 1137 | 3560 | 0.01539 |
| 2026-10-27T01:08:22Z | chat | muse-spark-1.3 | 452 | 753 | 2865 | 0.01285 |
| 2026-10-27T01:39:18Z | chat | muse-spark-1.3 | 455 | 753 | 2571 | 0.01161 |
| 2026-10-27T01:39:25Z | chat | muse-spark-1.3 | 457 | 753 | 2168 | 0.00990 |
| 2026-10-27T01:40:17Z | chat | muse-spark-1.3 | 72 | 1137 | 2586 | 0.01125 |
| 2026-10-27T01:40:29Z | chat | muse-spark-1.3 | 457 | 753 | 2794 | 0.01256 |
| 2026-10-27T01:40:35Z | chat | muse-spark-1.3 | 456 | 753 | 1518 | 0.00713 |
| 2026-10-27T01:40:40Z | chat | muse-spark-1.3 | 456 | 753 | 1521 | 0.00715 |
| 2026-10-27T01:40:47Z | chat | muse-spark-1.3 | 455 | 753 | 2016 | 0.00925 |
| 2026-10-27T01:40:55Z | chat | muse-spark-1.3 | 457 | 753 | 1630 | 0.00761 |
| 2026-10-27T01:41:06Z | chat | muse-spark-1.3 | 1209 | 0 | 2721 | 0.01308 |
| 2026-10-27T01:41:13Z | chat | muse-spark-1.3 | 454 | 753 | 2352 | 0.01068 |
| 2026-10-27T01:41:21Z | chat | muse-spark-1.3 | 71 | 1137 | 2412 | 0.01051 |
| 2026-10-27T01:41:30Z | chat | muse-spark-1.3 | 456 | 753 | 2678 | 0.01206 |
| 2026-10-27T01:41:38Z | chat | muse-spark-1.3 | 457 | 753 | 2580 | 0.01165 |
| 2026-10-27T01:41:47Z | chat | muse-spark-1.3 | 454 | 753 | 2238 | 0.01019 |
| 2026-10-27T01:41:59Z | chat | muse-spark-1.3 | 76 | 1137 | 3681 | 0.01591 |
| 2026-10-27T01:42:03Z | chat | muse-spark-1.3 | 1198 | 0 | 1145 | 0.00636 |
| 2026-10-27T01:42:10Z | chat | muse-spark-1.3 | 444 | 753 | 2264 | 0.01029 |
| 2026-10-27T01:42:16Z | chat | muse-spark-1.3 | 441 | 753 | 2032 | 0.00930 |
| 2026-10-27T01:42:21Z | chat | muse-spark-1.3 | 445 | 753 | 1682 | 0.00782 |
| 2026-10-27T01:42:28Z | chat | muse-spark-1.3 | 442 | 753 | 2232 | 0.01015 |
| 2026-10-27T01:42:33Z | chat | muse-spark-1.3 | 62 | 1137 | 1555 | 0.00686 |
| 2026-10-27T01:42:39Z | chat | muse-spark-1.3 | 1197 | 0 | 2251 | 0.01106 |
| 2026-10-27T01:42:45Z | chat | muse-spark-1.3 | 443 | 753 | 1909 | 0.00878 |
| 2026-10-27T01:42:52Z | chat | muse-spark-1.3 | 1196 | 0 | 1836 | 0.00930 |
| 2026-10-27T01:43:01Z | chat | muse-spark-1.3 | 1195 | 0 | 3108 | 0.01470 |
| 2026-10-27T01:43:07Z | chat | muse-spark-1.3 | 59 | 1137 | 1934 | 0.00846 |
| 2026-10-27T01:43:13Z | chat | muse-spark-1.3 | 443 | 753 | 1762 | 0.00816 |
| 2026-10-27T01:43:19Z | chat | muse-spark-1.3 | 58 | 1137 | 1944 | 0.00851 |
| 2026-10-27T01:43:24Z | chat | muse-spark-1.3 | 443 | 753 | 1843 | 0.00850 |
| 2026-10-27T01:43:33Z | chat | muse-spark-1.3 | 442 | 753 | 2244 | 0.01020 |
| 2026-10-27T01:43:42Z | chat | muse-spark-1.3 | 459 | 753 | 2837 | 0.01274 |
| 2026-10-27T01:43:51Z | chat | muse-spark-1.3 | 73 | 1137 | 2869 | 0.01246 |
| 2026-10-27T01:44:02Z | chat | muse-spark-1.3 | 458 | 753 | 3544 | 0.01575 |
| 2026-10-27T01:44:13Z | chat | muse-spark-1.3 | 457 | 753 | 3493 | 0.01553 |
| 2026-10-27T01:44:23Z | chat | muse-spark-1.3 | 459 | 753 | 2686 | 0.01210 |
| 2026-10-27T01:44:31Z | chat | muse-spark-1.3 | 459 | 753 | 2720 | 0.01225 |
| 2026-10-27T01:44:42Z | chat | muse-spark-1.3 | 457 | 753 | 3288 | 0.01466 |
| 2026-10-27T01:44:54Z | chat | muse-spark-1.3 | 457 | 753 | 3435 | 0.01528 |
| 2026-10-27T01:45:01Z | chat | muse-spark-1.3 | 1209 | 0 | 2628 | 0.01268 |
| 2026-10-27T01:45:06Z | chat | muse-spark-1.3 | 460 | 753 | 1789 | 0.00829 |
| 2026-10-27T01:45:12Z | chat | muse-spark-1.3 | 1210 | 0 | 1981 | 0.00993 |
| 2026-10-27T01:45:19Z | chat | muse-spark-1.3 | 457 | 753 | 2235 | 0.01018 |
| 2026-10-27T01:45:26Z | chat | muse-spark-1.3 | 456 | 753 | 2177 | 0.00994 |
| 2026-10-27T01:45:34Z | chat | muse-spark-1.3 | 457 | 753 | 2693 | 0.01213 |
| 2026-10-27T01:45:40Z | chat | muse-spark-1.3 | 456 | 753 | 1917 | 0.00883 |
| 2026-10-27T01:54:43Z | chat | muse-spark-1.3 | 28 | 0 | 1948 | 0.00831 |
| 2026-10-27T01:54:51Z | chat | muse-spark-1.3 | 28 | 0 | 1916 | 0.00818 |
| 2026-10-27T01:55:12Z | image | muse-image-1.0 | 0 | 0 | 0 | 0.01000 |
| 2026-10-27T01:55:30Z | vision | muse-spark-1.3 | 3382 | 0 | 3638 | 0.01969 |
| 2026-10-27T01:55:32Z | segment | sam-3.1 | 0 | 0 | 0 | 0.00250 |
| 2026-10-27T01:55:56Z | edit | muse-image-1.0 | 0 | 0 | 0 | 0.01000 |
| 2026-10-27T01:56:57Z | vision | muse-spark-1.3 | 1778 | 0 | 6070 | 0.02802 |
| 2026-10-27T01:57:16Z | vision | muse-spark-1.3 | 1776 | 0 | 5006 | 0.02350 |
| 2026-10-27T01:57:39Z | vision | muse-spark-1.3 | 909 | 867 | 6250 | 0.02783 |
| 2026-10-27T01:57:58Z | vision | muse-spark-1.3 | 1778 | 0 | 4392 | 0.02089 |
| 2026-10-27T01:58:21Z | vision | muse-spark-1.3 | 1778 | 0 | 5461 | 0.02543 |
| 2026-10-27T01:58:46Z | vision | muse-spark-1.3 | 1778 | 0 | 6131 | 0.02828 |
| 2026-10-27T02:03:56Z | chat | muse-spark-1.3 | 1058 | 0 | 1895 | 0.00938 |
| 2026-10-27T02:04:04Z | chat | muse-spark-1.3 | 1060 | 0 | 2810 | 0.01327 |
| 2026-10-27T02:04:17Z | chat | muse-spark-1.3 | 313 | 753 | 1923 | 0.00868 |
| 2026-10-27T02:04:21Z | chat | muse-spark-1.3 | 1054 | 0 | 1223 | 0.00652 |
| 2026-10-27T02:04:29Z | chat | muse-spark-1.3 | 1067 | 0 | 2297 | 0.01110 |
| 2026-10-27T02:04:36Z | chat | muse-spark-1.3 | 1073 | 0 | 2459 | 0.01179 |
| 2026-10-27T02:04:46Z | chat | muse-spark-1.3 | 1075 | 0 | 2616 | 0.01246 |
| 2026-10-27T02:04:55Z | chat | muse-spark-1.3 | 1081 | 0 | 2940 | 0.01385 |
| 2026-10-27T02:05:03Z | chat | muse-spark-1.3 | 1091 | 0 | 2722 | 0.01293 |
| 2026-10-27T02:05:11Z | chat | muse-spark-1.3 | 1099 | 0 | 2304 | 0.01117 |
| 2026-10-27T02:05:21Z | chat | muse-spark-1.3 | 335 | 753 | 3263 | 0.01440 |
| 2026-10-27T02:05:32Z | chat | muse-spark-1.3 | 87 | 1009 | 3322 | 0.01438 |
| 2026-10-27T02:05:41Z | chat | muse-spark-1.3 | 1106 | 0 | 3224 | 0.01508 |
| 2026-10-27T02:05:47Z | chat | muse-spark-1.3 | 1087 | 0 | 1653 | 0.00838 |
| 2026-10-27T02:05:53Z | chat | muse-spark-1.3 | 344 | 753 | 2087 | 0.00941 |
| 2026-10-27T02:06:01Z | chat | muse-spark-1.3 | 346 | 753 | 2465 | 0.01102 |
| 2026-10-27T02:12:30Z | chat | muse-spark-1.3 | 39 | 1009 | 1337 | 0.00588 |
| 2026-10-27T02:12:36Z | chat | muse-spark-1.3 | 1060 | 0 | 2037 | 0.00998 |
| 2026-10-27T02:12:40Z | chat | muse-spark-1.3 | 1062 | 0 | 1271 | 0.00673 |
| 2026-10-27T02:12:47Z | chat | muse-spark-1.3 | 1043 | 0 | 2467 | 0.01179 |
| 2026-10-27T02:12:52Z | chat | muse-spark-1.3 | 1064 | 0 | 1532 | 0.00784 |
| 2026-10-27T02:12:55Z | chat | muse-spark-1.3 | 1055 | 0 | 973 | 0.00545 |
| 2026-10-27T02:13:06Z | chat | muse-spark-1.3 | 322 | 753 | 3878 | 0.01700 |
| 2026-10-27T02:13:14Z | chat | muse-spark-1.3 | 1079 | 0 | 1591 | 0.00811 |
| 2026-10-27T02:13:23Z | chat | muse-spark-1.3 | 327 | 753 | 2817 | 0.01249 |
| 2026-10-27T02:13:33Z | chat | muse-spark-1.3 | 336 | 753 | 2886 | 0.01280 |
| 2026-10-27T02:13:39Z | chat | muse-spark-1.3 | 1097 | 0 | 2070 | 0.01017 |
| 2026-10-27T02:13:50Z | chat | muse-spark-1.3 | 347 | 753 | 3521 | 0.01551 |
| 2026-10-27T02:13:57Z | chat | muse-spark-1.3 | 1098 | 0 | 2543 | 0.01218 |
| 2026-10-27T02:14:06Z | chat | muse-spark-1.3 | 353 | 753 | 2733 | 0.01217 |
| 2026-10-27T02:14:15Z | chat | muse-spark-1.3 | 1109 | 0 | 2921 | 0.01380 |
| 2026-10-27T02:14:27Z | chat | muse-spark-1.3 | 348 | 753 | 3949 | 0.01733 |
| 2026-10-27T02:14:35Z | chat | muse-spark-1.3 | 1109 | 0 | 2363 | 0.01143 |
| 2026-10-27T02:14:42Z | chat | muse-spark-1.3 | 1108 | 0 | 2564 | 0.01228 |
| 2026-10-27T03:42:35Z | chat | muse-spark-1.3 | 1060 | 0 | 3133 | 0.01464 |
| 2026-10-27T03:42:47Z | chat | muse-spark-1.3 | 1057 | 0 | 1746 | 0.00874 |
| 2026-10-27T03:42:53Z | chat | muse-spark-1.3 | 306 | 753 | 1646 | 0.00749 |
| 2026-10-27T03:43:18Z | chat | muse-spark-1.3 | 1082 | 0 | 2385 | 0.01149 |
| 2026-10-27T03:43:36Z | chat | muse-spark-1.3 | 1104 | 0 | 1923 | 0.00955 |
| 2026-10-27T03:44:09Z | chat | muse-spark-1.3 | 1112 | 0 | 4466 | 0.02037 |
| 2026-10-27T03:44:20Z | chat | muse-spark-1.3 | 359 | 753 | 1784 | 0.00814 |
| 2026-10-27T03:44:37Z | chat | muse-spark-1.3 | 104 | 1009 | 5728 | 0.02463 |
| 2026-10-27T03:45:32Z | chat | muse-spark-1.3 | 1058 | 0 | 1939 | 0.00956 |
| 2026-10-27T03:45:36Z | chat | muse-spark-1.3 | 1064 | 0 | 1208 | 0.00646 |
| 2026-10-27T03:45:45Z | chat | muse-spark-1.3 | 1072 | 0 | 1185 | 0.00638 |
| 2026-10-27T03:45:51Z | chat | muse-spark-1.3 | 305 | 753 | 1737 | 0.00788 |
| 2026-10-27T03:46:00Z | chat | muse-spark-1.3 | 1075 | 0 | 2926 | 0.01378 |
| 2026-10-27T03:46:05Z | chat | muse-spark-1.3 | 1081 | 0 | 1442 | 0.00748 |
| 2026-10-27T03:46:15Z | chat | muse-spark-1.3 | 1081 | 0 | 2551 | 0.01219 |
| 2026-10-27T03:46:32Z | chat | muse-spark-1.3 | 1098 | 0 | 1442 | 0.00750 |
| 2026-10-27T03:46:38Z | chat | muse-spark-1.3 | 1103 | 0 | 1598 | 0.00817 |
| 2026-10-27T03:46:48Z | chat | muse-spark-1.3 | 1096 | 0 | 3074 | 0.01443 |
| 2026-10-27T03:47:02Z | chat | muse-spark-1.3 | 352 | 753 | 3860 | 0.01696 |
| 2026-10-27T03:47:10Z | chat | muse-spark-1.3 | 354 | 753 | 2606 | 0.01163 |
| 2026-10-27T03:47:26Z | chat | muse-spark-1.3 | 342 | 753 | 4744 | 0.02070 |
| 2026-10-27T03:47:34Z | chat | muse-spark-1.3 | 355 | 753 | 2285 | 0.01027 |
| 2026-10-27T03:47:44Z | chat | muse-spark-1.3 | 350 | 753 | 3307 | 0.01461 |
| 2026-10-27T04:44:25Z | chat | muse-spark-1.3 | 1023 | 0 | 1804 | 0.00895 |
| 2026-10-27T04:44:59Z | chat | muse-spark-1.3 | 138 | 881 | 2541 | 0.01110 |
| 2026-10-27T04:45:13Z | chat | muse-spark-1.3 | 1017 | 0 | 1692 | 0.00846 |
| 2026-10-27T04:45:28Z | chat | muse-spark-1.3 | 1023 | 0 | 2544 | 0.01209 |
| 2026-10-27T04:45:46Z | chat | muse-spark-1.3 | 1023 | 0 | 2488 | 0.01185 |
| 2026-10-27T04:46:11Z | chat | muse-spark-1.3 | 1019 | 0 | 4274 | 0.01944 |
| 2026-10-27T04:46:22Z | chat | muse-spark-1.3 | 1019 | 0 | 2337 | 0.01121 |
| 2026-10-27T04:46:41Z | chat | muse-spark-1.3 | 1019 | 0 | 2225 | 0.01073 |
| 2026-10-27T04:46:53Z | chat | muse-spark-1.3 | 1023 | 0 | 2610 | 0.01237 |
| 2026-10-27T04:47:41Z | chat | muse-spark-1.3 | 12 | 1009 | 1393 | 0.00609 |
| 2026-10-27T05:08:08Z | vision | muse-spark-1.3 | 1103 | 0 | 5199 | 0.02347 |
| 2026-10-27T06:02:00Z | chat | muse-spark-1.3 | 1057 | 0 | 1416 | 0.00734 |
| 2026-10-27T06:02:10Z | chat | muse-spark-1.3 | 1054 | 0 | 2328 | 0.01121 |
| 2026-10-27T06:02:23Z | chat | muse-spark-1.3 | 1056 | 0 | 1616 | 0.00819 |
| 2026-10-27T06:02:28Z | chat | muse-spark-1.3 | 1048 | 0 | 1594 | 0.00808 |
| 2026-10-27T06:03:35Z | chat | muse-spark-1.3 | 1075 | 0 | 2049 | 0.01005 |
| 2026-10-27T06:03:46Z | chat | muse-spark-1.3 | 1071 | 0 | 2922 | 0.01376 |
| 2026-10-27T06:04:04Z | chat | muse-spark-1.3 | 1099 | 0 | 2389 | 0.01153 |
| 2026-10-27T06:04:14Z | chat | muse-spark-1.3 | 1096 | 0 | 2300 | 0.01115 |
| 2026-10-27T06:04:36Z | chat | muse-spark-1.3 | 1098 | 0 | 2172 | 0.01060 |
| 2026-10-27T06:04:46Z | chat | muse-spark-1.3 | 1096 | 0 | 3015 | 0.01418 |
| 2026-10-27T06:05:02Z | chat | muse-spark-1.3 | 345 | 753 | 2032 | 0.00918 |
| 2026-10-27T06:05:08Z | chat | muse-spark-1.3 | 1094 | 0 | 1946 | 0.00964 |
| 2026-10-27T08:58:17Z | image | muse-image-1.0 | 0 | 0 | 0 | 0.01000 |
| 2026-10-27T08:58:21Z | segment | sam-3.1 | 0 | 0 | 0 | 0.00250 |
| 2026-10-27T09:32:54Z | chat | muse-spark-1.3 | 1053 | 0 | 1599 | 0.00811 |
| 2026-10-27T09:33:03Z | chat | muse-spark-1.3 | 1051 | 0 | 2652 | 0.01258 |
| 2026-10-27T09:33:14Z | chat | muse-spark-1.3 | 296 | 753 | 1791 | 0.00809 |
| 2026-10-27T09:33:20Z | chat | muse-spark-1.3 | 1046 | 0 | 1892 | 0.00935 |
| 2026-10-27T09:33:33Z | chat | muse-spark-1.3 | 1073 | 0 | 1820 | 0.00908 |
| 2026-10-27T09:33:43Z | chat | muse-spark-1.3 | 1075 | 0 | 3435 | 0.01594 |
| 2026-10-27T09:33:58Z | chat | muse-spark-1.3 | 1096 | 0 | 1825 | 0.00913 |
| 2026-10-27T09:34:03Z | chat | muse-spark-1.3 | 1096 | 0 | 1522 | 0.00784 |
| 2026-10-27T09:34:26Z | chat | muse-spark-1.3 | 1095 | 0 | 3833 | 0.01766 |
| 2026-10-27T09:34:35Z | chat | muse-spark-1.3 | 1100 | 0 | 2729 | 0.01297 |
| 2026-10-27T09:34:48Z | chat | muse-spark-1.3 | 1095 | 0 | 1728 | 0.00871 |
| 2026-10-27T09:34:57Z | chat | muse-spark-1.3 | 1093 | 0 | 2671 | 0.01272 |
| 2026-10-27T09:51:00Z | vision | muse-spark-1.3 | 2237 | 0 | 4594 | 0.02232 |
| 2026-10-27T09:51:19Z | vision | muse-spark-1.3 | 2237 | 0 | 4874 | 0.02351 |
| 2026-10-27T09:52:17Z | chat | muse-spark-1.3 | 1055 | 0 | 1574 | 0.00801 |
| 2026-10-27T09:52:24Z | chat | muse-spark-1.3 | 1055 | 0 | 1784 | 0.00890 |
| 2026-10-27T09:52:34Z | chat | muse-spark-1.3 | 1050 | 0 | 1262 | 0.00668 |
| 2026-10-27T09:52:42Z | chat | muse-spark-1.3 | 1049 | 0 | 2769 | 0.01308 |
| 2026-10-27T09:52:54Z | vision | muse-spark-1.3 | 1103 | 0 | 3781 | 0.01745 |
| 2026-10-27T09:53:00Z | chat | muse-spark-1.3 | 1074 | 0 | 2842 | 0.01342 |
| 2026-10-27T09:53:07Z | chat | muse-spark-1.3 | 191 | 881 | 2384 | 0.01050 |
| 2026-10-27T09:53:12Z | vision | muse-spark-1.3 | 1103 | 0 | 4720 | 0.02144 |
| 2026-10-27T09:53:21Z | chat | muse-spark-1.3 | 1093 | 0 | 2408 | 0.01160 |
| 2026-10-27T09:53:28Z | chat | muse-spark-1.3 | 1094 | 0 | 2194 | 0.01069 |
| 2026-10-27T09:53:46Z | chat | muse-spark-1.3 | 1097 | 0 | 2754 | 0.01308 |
| 2026-10-27T09:53:54Z | chat | muse-spark-1.3 | 1103 | 0 | 2816 | 0.01335 |
| 2026-10-27T09:54:08Z | chat | muse-spark-1.3 | 1100 | 0 | 2518 | 0.01208 |
| 2026-10-27T09:54:16Z | chat | muse-spark-1.3 | 1095 | 0 | 2602 | 0.01243 |
| 2026-10-27T09:58:26Z | chat | muse-spark-1.3 | 30 | 1009 | 1295 | 0.00569 |
| 2026-10-27T09:58:32Z | chat | muse-spark-1.3 | 1052 | 0 | 1796 | 0.00895 |
| 2026-10-27T09:58:37Z | chat | muse-spark-1.3 | 1055 | 0 | 1640 | 0.00829 |
| 2026-10-27T09:58:42Z | chat | muse-spark-1.3 | 25 | 1009 | 1181 | 0.00520 |
| 2026-10-27T09:58:47Z | chat | muse-spark-1.3 | 1049 | 0 | 1880 | 0.00930 |
| 2026-10-27T09:58:52Z | chat | muse-spark-1.3 | 1046 | 0 | 1380 | 0.00717 |
| 2026-10-27T09:59:01Z | chat | muse-spark-1.3 | 1065 | 0 | 3262 | 0.01519 |
| 2026-10-27T09:59:08Z | chat | muse-spark-1.3 | 1073 | 0 | 2103 | 0.01028 |
| 2026-10-27T09:59:16Z | chat | muse-spark-1.3 | 1073 | 0 | 3000 | 0.01409 |
| 2026-10-27T09:59:24Z | chat | muse-spark-1.3 | 70 | 1009 | 2605 | 0.01131 |
| 2026-10-27T09:59:30Z | chat | muse-spark-1.3 | 1090 | 0 | 1801 | 0.00902 |
| 2026-10-27T09:59:38Z | chat | muse-spark-1.3 | 1098 | 0 | 2635 | 0.01257 |
| 2026-10-27T09:59:45Z | chat | muse-spark-1.3 | 1086 | 0 | 2542 | 0.01216 |
| 2026-10-27T09:59:57Z | chat | muse-spark-1.3 | 1095 | 0 | 3353 | 0.01562 |
| 2026-10-27T10:00:05Z | chat | muse-spark-1.3 | 1101 | 0 | 2740 | 0.01302 |
| 2026-10-27T10:00:11Z | chat | muse-spark-1.3 | 76 | 1009 | 2133 | 0.00931 |
| 2026-10-27T10:00:18Z | chat | muse-spark-1.3 | 1096 | 0 | 2370 | 0.01144 |
| 2026-10-27T10:00:27Z | chat | muse-spark-1.3 | 1094 | 0 | 3121 | 0.01463 |

## 5. What this page does not claim

- It is a list price calculation over recorded token counts, not a copy of a bill. Meta's invoice is the authority; if the two disagree, the invoice wins.
- The hackathon credit grant (150 USD, `HACKATHON-BRIEF.md` section 3 and the waiver) is unconfirmed for this team, so this spend is charged against whatever payment method the account holds until that changes.
- No figure here includes the account's own charges outside this repository, or the manager's 2026-10-26 smoke call, which was recorded in `arananet/meta-hackathon/META-SMOKE-2026-10-26.txt`, not in this cache.
