import json, os
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEWS = ("photorealistic still frame from a local television news broadcast, shot on a broadcast camera, natural true-to-life colors, "
        "crisp focus, no text, no letters, no words, no logos, no captions, no watermark")
OUT = ("bright clear high desert daylight, soft sun key from camera left with gentle shadows on the right, open sky fill, "
       "Silver Springs Nevada, gray-green sagebrush, low bare brown hills")
STUDIO = ("bright modern local television news studio, soft key light from camera left, gentle fill, blue and warm practical lights "
          "blurred in the background, shallow depth of field")
FACE = "looking straight into the camera, face fully visible and well lit, lips gently closed, natural skin texture"
J = [
 ("anchor_a", 3101, f"medium close shot of a local TV news anchor, a man in his late fifties with short neat gray hair and a strong jaw, navy suit, white shirt, red tie, sitting at a glossy news desk, hands folded on the desk, {FACE}. {STUDIO}, a large blurred video wall behind him glowing blue"),
 ("anchor_b", 3102, f"medium close shot of a serious local TV news anchor, a man in his late fifties with short gray hair, navy suit, white shirt, dark red tie, seated at a glossy anchor desk, {FACE}. {STUDIO}, a large blurred blue video wall behind him"),
 ("anchor_w", 3103, f"wide shot of a bright local TV news studio set, a gray-haired male anchor in a navy suit seated alone at a long glossy curved anchor desk in the center, big blue video wall behind him, studio lights. {STUDIO}"),
 ("reporter_a", 3201, f"medium shot of a female TV field reporter in her thirties with shoulder-length brown hair, wearing a red rain jacket, holding a handheld news microphone with a plain black foam cover, standing in the middle of a two-lane desert highway covered by shallow floodwater up to her ankles, {FACE}. {OUT}"),
 ("reporter_b", 3202, f"medium shot of a female TV news field reporter in her thirties, brown hair, red rain jacket, holding a handheld microphone with a plain black foam cover, standing on a flooded two-lane desert highway, water over the asphalt around her boots, yellow center line visible under the water, {FACE}. {OUT}"),
 ("hwy", 3203, f"wide shot of a two-lane desert highway disappearing toward low brown hills, shallow floodwater spreading across the asphalt and the yellow center line, water spilling out of the sagebrush on both sides, a lone pickup truck stopped in the distance. {OUT}"),
 ("reservoir", 3301, f"aerial news helicopter shot of a large desert reservoir in Nevada, muddy water pouring UP over the top of a low brown hillside, defying gravity, waves climbing the slope, a small concrete dam below, sagebrush. {OUT}"),
 ("sage", 3302, f"close shot of round clumps of uprooted gray-green sagebrush bushes floating on calm shallow brown floodwater covering flat desert ground, reflections, low brown hills in the soft background. {OUT}"),
 ("sci_a", 3401, f"medium close shot of an older scientist in his late sixties with white hair and a short white beard, wire-rimmed glasses, tan cardigan over a blue collared shirt, standing in front of a whiteboard densely covered with scribbled blue and red marker diagrams of wavy water lines, arrows and a lake outline, {FACE}. a cluttered university office, daylight window key from the left, soft shadows on the right"),
 ("sci_b", 3402, f"medium close shot of an older male hydrologist about seventy with white hair, wire-rimmed glasses, brown corduroy jacket, standing beside a messy whiteboard full of scribbled marker diagrams, contour lines, arrows and wave sketches, {FACE}. university office, soft window light from the left"),
 ("rings", 3501, f"wide shot of bare brown desert hills above a Nevada valley with clear horizontal ancient lake shoreline terraces etched across the slopes like bathtub rings, a new flat lake of blue water filling the valley floor and creeping up toward the lowest ring. {OUT}"),
 ("res_a", 3601, f"medium shot of a grizzled man in his sixties with a gray stubbly beard and a sun-weathered face, faded trucker cap, wearing a bright orange life jacket over a flannel shirt, sitting relaxed in a folding lawn chair in the front yard of a single-wide manufactured home, ankle-deep floodwater around the chair legs, {FACE}. {OUT}"),
 ("res_b", 3602, f"medium close shot of a weathered old desert local in his sixties, gray beard, faded cap, orange life vest over a plaid flannel shirt, sitting in a folding lawn chair in his yard with floodwater around him, a manufactured home behind, {FACE}. {OUT}"),
 ("pontoon", 3701, f"a pontoon boat on a trailer parked in the gravel driveway of a single-wide manufactured home in a small high desert town, shallow floodwater lapping at the trailer tires, a pickup truck, chain-link fence. {OUT}"),
 ("fish", 3801, f"a huge prehistoric armored fish like a giant sturgeon, ten feet long, swimming down a flooded residential street in a small Nevada desert town, its armored back and tall dorsal fin breaking the brown water, ripples and wake, small houses, mailboxes and a parked pickup truck. {OUT}"),
 ("aerial", 3901, f"aerial news helicopter shot looking down on a small high desert town, Silver Springs Nevada, a highway running through it, sheets of shining floodwater spreading across the streets and yards, sagebrush flats and low brown hills all around. {OUT}"),
]
json.dump([{"out": f"{P}/stills/{n}.png", "prompt": p + ". " + NEWS, "w": 768, "h": 1344, "seed": s} for n, s, p in J], open(f"{P}/stills_jobs.json", "w"), indent=1)
print(len(J))
