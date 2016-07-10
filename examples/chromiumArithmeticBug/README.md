Fixing a bug in Chromium (Blink) with CCTDB
=========

[crbug.com/604331](https://crbug.com/604331) is a bug where one input ([bug.html](bug.html)) crashes but a slight variation of the testcase ([nobug.html](nobug.html)) does not crash. This crash occurs during painting but the culprit is likely in  layout code. Unfortunately, layout is [large and complex](https://cs.chromium.org/chromium/src/third_party/WebKit/Source/core/layout/) so tracking this bug down is like finding a needle in a haystack.

This example walks through a real-world bug using CCTDB.

Scripting LLDB and CCTDB
--------

To make things easier, start with a command to dump a Calling Context Tree (CCT) from Chromium:
```
lldb \
    -o "command script import recordCommand.py" \
    -o "target create 'chromium/src/out/Debug/chromium'"
    -o "settings set -- target.run-args  '--no-sandbox' '--single-process' 'nobug.html'"
    -o "breakpoint set --name FrameView::layout()" \
    -o "run" \
    -o "record --output=nobug.json --regex '^blink::'" \
    -o "quit"
```
This script uses lldb's `-o` option to chain several commands together which record a CCT starting at `FrameView::layout()` and write the result to `nobug.json`. A regular expression (`'^blink::'`) is used to improve recording speed by staying inside the `blink::` namespace.

Narrowing in on the bug
--------

Begin by running the above command twice with nobug.html and bug.html (full command omitted below to save space):
```
> lldb ... nobug.html ... nobug.json ...
  Wrote recording to 'nobug.json'
> lldb ... bug.html ... bug.json ...
  Wrote recording to 'bug.json'
```

Then use the `compare.py` script to analyze the two CCTs:
```
> ./compare.py nobug.json bug.json
bug.json diverged from nobug.json in 7 places:
  FloatingObjects::set() which was called by LayoutBlockFlow::rebuildFloatsFromIntruding()
  LayoutBlockFlow::addIntrudingFloats(...) which was called by LayoutBlockFlow::rebuildFloatsFromIntruding()
  LayoutBlockFlow::lastRootBox() which was called by LayoutBlockFlow::markLinesDirtyInBlockRange(...)
  LayoutUnit::LayoutUnit() which was called by LayoutBlockFlow::rebuildFloatsFromIntruding() (2 instances)
  LayoutBlockFlow::logicalBottomForFloat(...) which was called by LayoutBlockFlow::rebuildFloatsFromIntruding()
  FloatingObject::layoutObject() which was called by LayoutBlockFlow::rebuildFloatsFromIntruding()
```

Somehow `bug.html` is causing different calls to be made inside `LayoutBlockFlow::rebuildFloatsFromIntruding()`.

Fixing the bug
--------

Looking at [LayoutBlockFlow.cpp](https://cs.chromium.org/chromium/src/third_party/WebKit/Source/core/layout/LayoutBlockFlow.cpp), `addIntrudingFloats` is only getting called when the bug is present.

```
void LayoutBlockFlow::rebuildFloatsFromIntruding()
{
    ...
    LayoutUnit logicalTopOffset = logicalTop();
    ...
    // Add overhanging floats from the previous LayoutBlockFlow...
    if (prev) {
        LayoutBlockFlow* blockFlow = toLayoutBlockFlow(prev);
        logicalTopOffset -= blockFlow->logicalTop();
        if (blockFlow->lowestFloatLogicalBottom() > logicalTopOffset)
            addIntrudingFloats(blockFlow, LayoutUnit(), logicalTopOffset);
    }
    ...
```

Chromium uses fixed-point units (`LayoutUnit`) with [saturated arithmetic](https://en.wikipedia.org/wiki/Saturation_arithmetic) (i.e., max + 100 = max). The bug is that two huge values are being compared and their difference is incorrect due to saturated arithmetic. Here's a simpler example which demonstrates the bug:
```
   LayoutUnit a = (LayoutUnit::max() + 1000);
   LayoutUnit b = (LayoutUnit::max() + 10);
   if (a > b)
        // This is hit if normal arithmetic is used.
   else
        // This is hit when saturated arithmetic is used because a == b!
```

The fix for this bug landed in [6c961fe1112914b9d63d6551e31b96c415dfb83f](https://crrev.com/6c961fe1112914b9d63d6551e31b96c415dfb83f) and simply re-ordered the operations to avoid a saturated arithmetic bug.

Wrapup
--------
This is a real example where locating the root-cause of a bug is time consuming. CCTDB recordings can take a long time to generate (each run above took ~30 minutes) but this is much faster than a Chromium engineer manually locating the bug (roughly ~12 hours). CCTDB would have saved over a day of debugging!
