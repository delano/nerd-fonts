// Nerd Fonts Version: 3.5.1
// Script Version: 1.0.0
//
// Render a provenance sample through CoreText and report which glyphs it chose.
//
// HarfBuzz (hb-view) and FreeType are what generate-provenance-example.sh uses,
// but macOS applications shape and rasterise through CoreText, which behaves
// differently in two ways that matter for the provenance marks:
//
//   1. It drops variation selectors, so only the PUA-encoded line of the sample
//      carries a mark (see "Observed behaviour" in src/glyphs/provenance/README.md).
//   2. It antialiases diagonal strokes to grey where FreeType keeps them dark,
//      so a mark that is visible in hb-view can vanish here at terminal sizes.
//
// Usage:
//   swift bin/scripts/render-provenance-coretext.swift FONT SAMPLE OUT.png [SIZE]
//
//   FONT    path to a .ttf/.otf, or name:PostScriptName to use an installed font
//           (the resolved file path is printed, which shows whether the system
//           picked up a reinstalled font or a stale copy)
//   SAMPLE  text file, one line per provenance state, as written by
//           generate-provenance-example.sh (temp/provenance-example/sample.txt)
//   SIZE    point size, default 16; also render at 40 to see the shapes
//
// For repeated runs compile it once: swiftc -O -o temp/ctrender bin/scripts/render-provenance-coretext.swift
//
// Each line reports the PostScript name of the font CoreText actually used and
// the glyph name of its first non-space glyph, so a fallback font or a dropped
// selector shows up in the text output as well as in the image. macOS only.

import Foundation
import CoreText
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers

func fail(_ message: String) -> Never {
    FileHandle.standardError.write((message + "\n").data(using: .utf8)!)
    exit(1)
}

let args = CommandLine.arguments
if args.count < 4 || args.count > 5 {
    fail("usage: \(args[0]) FONT|name:PostScriptName SAMPLE OUT.png [SIZE]")
}
let spec = args[1], samplePath = args[2], outPath = args[3]
guard let sizeValue = Double(args.count > 4 ? args[4] : "16"), sizeValue > 0 else { fail("SIZE must be a positive number") }
let size = CGFloat(sizeValue)

var font: CTFont
if spec.hasPrefix("name:") {
    let name = String(spec.dropFirst(5))
    font = CTFontCreateWithName(name as CFString, size, nil)
    if CTFontCopyPostScriptName(font) as String != name {
        fail("no installed font named \(name), CoreText substituted \(CTFontCopyPostScriptName(font))")
    }
} else {
    let url = URL(fileURLWithPath: spec) as CFURL
    guard let descs = CTFontManagerCreateFontDescriptorsFromURL(url) as? [CTFontDescriptor], let d = descs.first else {
        fail("CoreText could not load a font from \(spec)")
    }
    font = CTFontCreateWithFontDescriptor(d, size, nil)
}
let desc = CTFontCopyFontDescriptor(font)
let resolved = (CTFontDescriptorCopyAttribute(desc, kCTFontURLAttribute) as? URL)?.path ?? "?"
print("font: \(CTFontCopyPostScriptName(font)) size: \(sizeValue) file: \(resolved)")

guard let text = try? String(contentsOfFile: samplePath, encoding: .utf8) else { fail("cannot read \(samplePath)") }
let lines = text.split(separator: "\n").map(String.init).filter { !$0.isEmpty }
if lines.isEmpty { fail("\(samplePath) is empty") }

let width = Int(size * 36), lineH = Int(size * 1.4), height = lineH * lines.count + Int(size)
let cs = CGColorSpaceCreateDeviceRGB()
guard let ctx = CGContext(data: nil, width: width, height: height, bitsPerComponent: 8, bytesPerRow: 0,
                          space: cs, bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else { fail("cannot create bitmap") }
ctx.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
ctx.fill(CGRect(x: 0, y: 0, width: width, height: height))
ctx.setFillColor(CGColor(red: 0, green: 0, blue: 0, alpha: 1))

for (i, s) in lines.enumerated() {
    let attr = NSAttributedString(string: s, attributes: [kCTFontAttributeName as NSAttributedString.Key: font])
    let line = CTLineCreateWithAttributedString(attr)
    var report = Set<String>()
    for run in CTLineGetGlyphRuns(line) as! [CTRun] {
        let attrs = CTRunGetAttributes(run) as! [NSAttributedString.Key: Any]
        let runFont = attrs[kCTFontAttributeName as NSAttributedString.Key] as! CTFont
        var glyphs = [CGGlyph](repeating: 0, count: CTRunGetGlyphCount(run))
        CTRunGetGlyphs(run, CFRangeMake(0, 0), &glyphs)
        report.insert(CTFontCopyPostScriptName(runFont) as String)
        if let g = glyphs.first(where: { $0 != 0 }), let name = CTFontCopyNameForGlyph(runFont, g) {
            report.insert("first-glyph:\(name)")
        }
    }
    print("line \(i): \(report.sorted().joined(separator: " "))")
    ctx.textPosition = CGPoint(x: 10, y: CGFloat(height - Int(size) - i * lineH))
    CTLineDraw(line, ctx)
}

guard let image = ctx.makeImage(),
      let dest = CGImageDestinationCreateWithURL(URL(fileURLWithPath: outPath) as CFURL, UTType.png.identifier as CFString, 1, nil) else {
    fail("cannot write \(outPath)")
}
CGImageDestinationAddImage(dest, image, nil)
if !CGImageDestinationFinalize(dest) { fail("cannot write \(outPath)") }
print("wrote \(outPath)")
