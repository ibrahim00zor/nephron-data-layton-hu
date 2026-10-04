// Look at a page the way Safari draws it, without touching Safari.
//
// The app is developed against Chromium; Safari (WebKit) once drew a page with the lines of
// every chart missing, and nobody could see it from here. This renders a URL in WebKit, off
// screen, and saves a picture.
//
//   swift tools/webkit_shot.swift <url> <out.png> [height] [javascript to run before the picture]
//   swift tools/webkit_shot.swift http://localhost:8501/segment_profile /tmp/segment.png
//
// The view is not visible, so CSS animations stay at their first frame: to look at the Home
// figure, switch them off with the javascript argument, e.g.
//   "const s = document.createElement('style'); s.textContent = '.nd-plate * { animation: none !important; }'; document.head.appendChild(s); 'ok'"
// Web fonts may not have loaded in the picture; that is the tool, not the page.
import Cocoa
import WebKit

let args = CommandLine.arguments
let url = URL(string: args[1])!
let out = args[2]
let height = args.count > 3 ? Double(args[3]) ?? 900 : 900
let script = args.count > 4 ? args[4] : ""
let width = 1440.0

let app = NSApplication.shared
app.setActivationPolicy(.prohibited)          // no Dock icon, never takes focus

let web = WKWebView(frame: NSRect(x: 0, y: 0, width: width, height: height),
                    configuration: WKWebViewConfiguration())
let window = NSWindow(contentRect: NSRect(x: -4000, y: -4000, width: width, height: height),
                      styleMask: [.borderless], backing: .buffered, defer: false)
window.contentView = web
window.orderBack(nil)
web.load(URLRequest(url: url))

func picture() {
    web.takeSnapshot(with: WKSnapshotConfiguration()) { image, error in
        if let image = image, let tiff = image.tiffRepresentation,
           let rep = NSBitmapImageRep(data: tiff),
           let png = rep.representation(using: .png, properties: [:]) {
            try? png.write(to: URL(fileURLWithPath: out))
            print("saved \(out)")
        } else {
            print("failed: \(String(describing: error))")
        }
        exit(0)
    }
}

DispatchQueue.main.asyncAfter(deadline: .now() + 13) {
    if script.isEmpty { picture(); return }
    web.evaluateJavaScript(script) { result, error in
        if let result = result { print("js: \(result)") }
        if let error = error { print("js error: \(error.localizedDescription)") }
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.5) { picture() }
    }
}
app.run()
