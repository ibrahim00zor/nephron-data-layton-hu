// Drive a page in Safari's engine, off screen: point at it, click it, time how long it takes
// to paint, and take pictures along the way.
//
// webkit_shot.swift takes one picture. This runs a list of steps, so that what a page does
// under the pointer can be looked at (and measured) in WebKit without touching Safari:
//
//   swift tools/webkit_drive.swift <url> [width x height] <step> <step> ...
//
//   wait:SECONDS        let the page settle
//   js:CODE             run JavaScript in the page; the result is printed
//   move:X,Y            move the pointer there (CSS pixels from the top left of the view)
//   click:X,Y           press and release the left button there
//   shot:FILE.png       save a picture of the view
//   paint:N             paint the view N times and print how long each took (ms)
//   live                (first step only) run the page as if it were being looked at
//
//   swift tools/webkit_drive.swift http://localhost:8501/ 1440x900 wait:9 paint:6 \
//         move:900,400 wait:0.4 shot:/tmp/hover.png
//
// "paint" asks WebKit for a snapshot, which draws the visible part of the page again from
// nothing. It is not a frame rate, but it is what a frame costs when everything on screen
// has to be redrawn, and it moves with the things that make a page stutter in Safari
// (filters, masks, images that are drawings).
import Cocoa
import WebKit

var args = Array(CommandLine.arguments.dropFirst())
guard args.count >= 2, let url = URL(string: args.removeFirst()) else {
    print("usage: webkit_drive.swift <url> [WxH] <step>...")
    exit(2)
}
var width = 1440.0, height = 900.0
if let size = args.first, size.range(of: #"^\d+x\d+$"#, options: .regularExpression) != nil {
    let parts = size.split(separator: "x").map { Double($0)! }
    width = parts[0]; height = parts[1]
    args.removeFirst()
}
var steps = args

let app = NSApplication.shared
app.setActivationPolicy(.prohibited)

let configuration = WKWebViewConfiguration()
if #available(macOS 14.0, *) {
    configuration.preferences.inactiveSchedulingPolicy = .none
}
let web = WKWebView(frame: NSRect(x: 0, y: 0, width: width, height: height), configuration: configuration)
// With "live" as the first step the window is put on the screen, fully transparent and deaf
// to the mouse: nothing is seen and nothing is in the way, but WebKit treats the page as one
// that is being looked at, so animations run and frames are produced at the rate of the
// display. Without it the window is far off screen: animations stay on their first frame.
let live = steps.first == "live"
if live { steps.removeFirst() }
let window = NSWindow(contentRect: NSRect(x: live ? 0 : -4000, y: live ? 0 : -4000, width: width, height: height),
                      styleMask: [.borderless], backing: .buffered, defer: false)
window.contentView = web
if live {
    window.alphaValue = 0
    window.ignoresMouseEvents = true
    window.level = .floating
    window.orderFrontRegardless()
} else {
    window.orderBack(nil)
}
web.load(URLRequest(url: url))

func mouse(_ type: NSEvent.EventType, _ x: Double, _ y: Double, clicks: Int = 0) {
    // the view is not flipped: its origin is at the bottom left
    let point = NSPoint(x: x, y: height - y)
    guard let event = NSEvent.mouseEvent(
        with: type, location: point, modifierFlags: [], timestamp: ProcessInfo.processInfo.systemUptime,
        windowNumber: window.windowNumber, context: nil, eventNumber: 0, clickCount: clicks, pressure: clicks > 0 ? 1 : 0)
    else { return }
    switch type {
    case .mouseMoved: web.mouseMoved(with: event)
    case .leftMouseDown: web.mouseDown(with: event)
    case .leftMouseUp: web.mouseUp(with: event)
    default: break
    }
}

func snapshot(_ done: @escaping (NSImage?) -> Void) {
    web.takeSnapshot(with: WKSnapshotConfiguration()) { image, _ in done(image) }
}

func after(_ seconds: Double, _ block: @escaping () -> Void) {
    DispatchQueue.main.asyncAfter(deadline: .now() + seconds, execute: block)
}

func paint(_ left: Int, _ times: [Double], _ done: @escaping ([Double]) -> Void) {
    if left == 0 { done(times); return }
    let start = CFAbsoluteTimeGetCurrent()
    snapshot { _ in
        let took = (CFAbsoluteTimeGetCurrent() - start) * 1000
        after(0.05) { paint(left - 1, times + [took], done) }
    }
}

func next() {
    if steps.isEmpty { exit(0) }
    let step = steps.removeFirst()
    let name = step.split(separator: ":", maxSplits: 1).first.map(String.init) ?? step
    let value = step.contains(":") ? String(step[step.index(after: step.firstIndex(of: ":")!)...]) : ""
    let point = value.split(separator: ",").compactMap { Double($0) }
    switch name {
    case "wait":
        after(Double(value) ?? 1) { next() }
    case "js":
        web.evaluateJavaScript(value) { result, error in
            if let result = result { print("js: \(result)") }
            if let error = error { print("js error: \(error.localizedDescription)") }
            next()
        }
    case "move" where point.count == 2:
        mouse(.mouseMoved, point[0], point[1])
        after(0.05) { next() }
    case "click" where point.count == 2:
        mouse(.mouseMoved, point[0], point[1])
        after(0.05) {
            mouse(.leftMouseDown, point[0], point[1], clicks: 1)
            after(0.04) {
                mouse(.leftMouseUp, point[0], point[1], clicks: 1)
                after(0.05) { next() }
            }
        }
    case "shot":
        snapshot { image in
            if let image = image, let tiff = image.tiffRepresentation,
               let rep = NSBitmapImageRep(data: tiff),
               let png = rep.representation(using: .png, properties: [:]) {
                try? png.write(to: URL(fileURLWithPath: value))
                print("saved \(value)")
            } else {
                print("failed: \(value)")
            }
            next()
        }
    case "paint":
        paint(Int(value) ?? 5, []) { times in
            let sorted = times.sorted()
            let median = sorted[sorted.count / 2]
            print("paint ms: " + times.map { String(format: "%.0f", $0) }.joined(separator: " ")
                  + String(format: "   median %.0f", median))
            next()
        }
    default:
        print("unknown step: \(step)")
        next()
    }
}

after(1.0) { next() }
app.run()
