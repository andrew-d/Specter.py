# To-Do List

## High-Priority

- Get tests for all the major functionality:
  - Opening pages
  - Waiting for load on multiple frames
  - Switching between frames
  - Setting field values
  - Keyboard/mouse events
- Centralize configuration - e.g. SSL errors live on the page, headers in
  individual open() calls, and so on.
- Support loading cookies
- Injecting JavaScript into pages
  - Need to support keeping it after the `window` object has been cleared.
  - Should support both code (as a string) and includes (as a URL).

## Medium-Priority

- Change User-Agent
- Scroll to location
- Support for multiple different windows (i.e. different QWebPages in single
  instance of Specter)
  - Related: ability to control whether a window opens in a new page or not
- File downloads
- Screenshots / PDF rendering
- Disk cache
- Better plugin support
- Proxies
- Hit testing elements from screen coordinates

## To Investigate

- RPC between browser and JS?
- Can we mimic PhantomJS and be 100% headless?
- Prebuilt library of User-Agents to select from?
