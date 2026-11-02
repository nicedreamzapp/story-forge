// face_area: largest human-face box as a fraction of the frame, per image (Apple Vision, on-device).
// usage: face_area img1.png [img2.png ...]   -> prints "<path> <fraction> <count>" per image
import Foundation
import Vision
import ImageIO
for path in CommandLine.arguments.dropFirst() {
    guard let src = CGImageSourceCreateWithURL(URL(fileURLWithPath: path) as CFURL, nil),
          let img = CGImageSourceCreateImageAtIndex(src, 0, nil) else { print("\(path) -1 0"); continue }
    let req = VNDetectFaceRectanglesRequest()
    try? VNImageRequestHandler(cgImage: img, options: [:]).perform([req])
    let faces = req.results ?? []
    let best = faces.map { Double($0.boundingBox.width * $0.boundingBox.height) }.max() ?? 0
    print("\(path) \(String(format: "%.4f", best)) \(faces.count)")
}
