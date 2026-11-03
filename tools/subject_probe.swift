// subject_probe: where the subject is in each frame, for subject-aware reframing (Apple Vision, on-device).
// usage: subject_probe img1.png [img2.png ...]
// prints one JSON object per image, boxes normalized 0..1 with the origin at the TOP-LEFT:
// {"path": "...", "faces": [[x,y,w,h,conf]], "humans": [[x,y,w,h,conf]], "saliency": [[x,y,w,h,conf]],
//  "objects": [[x,y,w,h,conf]], "text": [[x,y,w,h,conf,chars]]}
// faces = VNDetectFaceRectangles, humans = VNDetectHumanRectangles (full body), saliency = attention-based
// salient objects, objects = objectness-based salient objects. Cartoon / animal faces are often missed:
// saliency is the fallback the reframer uses then.
import Foundation
import Vision
import ImageIO

func box(_ r: CGRect, _ c: Float) -> [Double] {
    return [Double(r.minX), Double(1 - r.maxY), Double(r.width), Double(r.height), Double(c)]
}
func fmt(_ bs: [[Double]]) -> String {
    return "[" + bs.map { "[" + $0.map { String(format: "%.4f", $0) }.joined(separator: ",") + "]" }.joined(separator: ",") + "]"
}
for path in CommandLine.arguments.dropFirst() {
    guard let src = CGImageSourceCreateWithURL(URL(fileURLWithPath: path) as CFURL, nil),
          let img = CGImageSourceCreateImageAtIndex(src, 0, nil) else {
        print("{\"path\": \"\(path)\", \"error\": \"unreadable\"}"); continue
    }
    let faceReq = VNDetectFaceRectanglesRequest()
    let humanReq = VNDetectHumanRectanglesRequest()
    humanReq.upperBodyOnly = false
    let attReq = VNGenerateAttentionBasedSaliencyImageRequest()
    let objReq = VNGenerateObjectnessBasedSaliencyImageRequest()
    let textReq = VNRecognizeTextRequest()
    textReq.recognitionLevel = .fast
    textReq.usesLanguageCorrection = false
    try? VNImageRequestHandler(cgImage: img, options: [:]).perform([faceReq, humanReq, attReq, objReq, textReq])
    let texts: [[Double]] = (textReq.results ?? []).map {
        let n = Double($0.topCandidates(1).first?.string.count ?? 0)
        return box($0.boundingBox, $0.confidence) + [n]
    }
    let faces = (faceReq.results ?? []).map { box($0.boundingBox, $0.confidence) }
    let humans = (humanReq.results ?? []).map { box($0.boundingBox, $0.confidence) }
    var sal: [[Double]] = []
    if let o = attReq.results?.first as? VNSaliencyImageObservation {
        sal = (o.salientObjects ?? []).map { box($0.boundingBox, $0.confidence) }
    }
    var objs: [[Double]] = []
    if let o = objReq.results?.first as? VNSaliencyImageObservation {
        objs = (o.salientObjects ?? []).map { box($0.boundingBox, $0.confidence) }
    }
    let p = path.replacingOccurrences(of: "\"", with: "\\\"")
    print("{\"path\": \"\(p)\", \"faces\": \(fmt(faces)), \"humans\": \(fmt(humans)), \"saliency\": \(fmt(sal)), \"objects\": \(fmt(objs)), \"text\": \(fmt(texts))}")
}
