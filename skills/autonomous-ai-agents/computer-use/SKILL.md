---
name: computer-use
description: |
  Drive the user's desktop in the background — clicking, typing,
  scrolling, dragging — without stealing the cursor, keyboard focus,
  or switching virtual desktops / Spaces. Cross-platform: macOS,
  Windows, Linux. Works with any tool-capable model. Load this skill
  whenever the `computer_use` tool is available.
version: 2.0.0
author: Arcen Agent (ported from Hermes Agent)
platforms: [macos, windows, linux]
metadata:
  arcen:
    tags: [computer-use, desktop, automation, gui, cross-platform]
    category: desktop
    related_skills: []
---

# Computer Use (Universal, Any-Model, Cross-Platform)

You have a `computer_use` tool that drives the user's desktop in the
**background** — your actions do NOT move the user's cursor, steal
keyboard focus, or switch virtual desktops / Spaces. The user can keep
typing in their editor while you click around in a browser in another
window. This is the opposite of pyautogui-style automation.

Everything here works with any tool-capable model — Claude, GPT, Gemini,
or an open model on a local OpenAI-compatible endpoint. There is no
provider-native schema to learn.

> **macOS-specific:** For Apple-native automation (AppleScript, Shortcuts,
> iMessage, etc.) see the `apple/macos-computer-use` skill. This skill
> focuses on cross-platform GUI automation.

## The Canonical Workflow

**Step 1 — Capture first.** Almost every task starts with:

```
computer_use(action="capture", mode="som", app="<the app you're driving>")
```

Returns a screenshot with numbered overlays on every interactable
element AND an AX-tree index like:

```
#1  AXButton 'Back' @ (12, 80, 28, 28) [Chrome]
#2  AXTextField 'Address bar' @ (80, 80, 900, 32) [Chrome]
#7  Link 'Sign In' @ (900, 420, 80, 24) [Chrome]
...
```

The role names match the host platform's accessibility framework
(`AXButton` on macOS, `Button` on Windows UIA, `push button` on Linux
AT-SPI) — treat them as labels, not as strict types.

**Step 2 — Click by element index.** This is the single most important
habit:

```
computer_use(action="click", element=7)
```

Much more reliable than pixel coordinates for every model.

**Step 3 — Verify.** After any state-changing action, re-capture. You
can save a round-trip by asking for the post-action capture inline:

```
computer_use(action="click", element=7, capture_after=True)
```

## Capture Modes

| `mode` | Returns | Best for |
|---|---|---|
| `som` (default) | Screenshot + numbered overlays + AX index | Vision models; preferred default |
| `vision` | Plain screenshot | When SOM overlay interferes |
| `ax` | AX tree only, no image | Text-only models |

## Actions

```
capture           mode=som|vision|ax   app=…  (default: current app)
click             element=N     OR     coordinate=[x, y]    button=left|right|middle
double_click      element=N     OR     coordinate=[x, y]
right_click       element=N     OR     coordinate=[x, y]
middle_click      element=N     OR     coordinate=[x, y]
drag              from_element=N, to_element=M  (or from/to_coordinate)
scroll            direction=up|down|left|right   amount=3 (ticks)
type              text="…"
key               keys="<save shortcut>" | "return" | "escape" | "<modifier>+t"
wait              seconds=0.5
list_apps
focus_app         app="<app name>"   raise_window=false   (default: don't raise)
```

All actions accept optional `capture_after=True` to get a follow-up
screenshot in the same tool call. All actions that target an element
accept `modifiers=[…]` for held keys.

## The Verify → Escalate Ladder (Background-First)

The driver delivers input in the **background** by default (no focus steal),
but that is the first rung, not the only one. Every input action returns a
structured verdict; read it and climb only when the driver tells you to.

Returned fields:
- `effect`: `"confirmed"` (driver read the result back — done),
  `"unverifiable"` (delivered, but confirm by re-capturing), or
  `"suspected_noop"` (ran but almost certainly did nothing).
- `escalation`: `{recommended: "px" | "foreground" | "page", reason}` —
  present only when there's a next rung to try.
- `code`: a structured refusal like `"background_unavailable"` or
  `"foreground_unsupported"`.
- `verified`: `true` only on AX read-back.

Walk it in order:

1. **Element, background (default).** `click(element=N)`. If
   `effect:"confirmed"`, you're done.
2. **Pixel, background.** On `escalation.recommended == "px"` (or a
   degraded capture with an empty element list), click by
   `coordinate=[x,y]` read off the screenshot instead of `element`.
3. **Foreground.** On `escalation.recommended == "foreground"`,
   `code:"background_unavailable"`, or a pixel click that still didn't
   land, re-issue the SAME action with `delivery_mode="foreground"`.
   This briefly raises the window and restores focus after.
   Only use foreground when the user isn't actively working.

```
computer_use(action="click", element=7)
# → {effect: "suspected_noop", escalation: {recommended: "foreground", ...}}
computer_use(action="click", element=7, delivery_mode="foreground")
# → {effect: "unverifiable", ...}   then re-capture to confirm
```

**Escalate as a REACTION to a returned signal, never as a prediction.**

## Rules for Background Automation

- **Never foreground unless signaled.** Foreground steals focus from
  whatever the user is doing. Only escalate when `effect:"suspected_noop"`
  or `code:"background_unavailable"` tells you to.
- **Always wait for visual feedback.** Don't fire multiple clicks before
  confirming the previous one landed. Use `capture_after=True`.
- **Prefer element index over coordinates.** Element indices are layout-
  stable; pixel coordinates break on DPI change or window resize.
- **Stop on repeated `suspected_noop`.** If the same element returns
  `suspected_noop` after background AND foreground, the app is likely using
  a non-standard input mechanism. Report to the user and ask for guidance.

## Cross-Platform Notes

| Platform | Accessibility Framework | Notes |
|---|---|---|
| macOS | AX (`AXButton`, `AXTextField`, …) | Most reliable — AX read-back gives `verified: true` |
| Windows | UIA (`Button`, `Edit`, …) | UIA read-back available on most native apps |
| Linux | AT-SPI (`push button`, `entry`, …) | Background delivery works via AT-SPI; X11 apps may need `xdotool` fallback |

## Common Patterns

### Open an application

```
list_apps                          # see what's running
focus_app(app="Google Chrome")     # bring to focus (background)
# OR
computer_use(action="key", keys="cmd+space")  # macOS Spotlight
computer_use(action="type", text="Google Chrome")
computer_use(action="key", keys="return")
```

### Fill a web form

```
# 1. Capture to see elements
computer_use(action="capture", mode="som", app="Google Chrome")
# → screenshot shows #12 = name field, #15 = email, #20 = submit

# 2. Fill fields
computer_use(action="click", element=12)
computer_use(action="type", text="John Doe")
computer_use(action="click", element=15)
computer_use(action="type", text="john@example.com")

# 3. Submit and verify
computer_use(action="click", element=20, capture_after=True)
```

### Scroll a document

```
computer_use(action="scroll", direction="down", amount=5)
computer_use(action="capture", mode="vision")  # verify new position
```

### Keyboard shortcuts

```
computer_use(action="key", keys="cmd+s")      # Save (macOS)
computer_use(action="key", keys="ctrl+s")     # Save (Windows/Linux)
computer_use(action="key", keys="cmd+shift+t") # Reopen closed tab
```
