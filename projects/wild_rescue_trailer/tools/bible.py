"""HANK & DOUG'S WILD RESCUE: the fixed style strings and character/set descriptions.
Every prompt in this film is built from these strings WORD FOR WORD (stage 03 rule). Never paraphrase them."""

STYLE_DAY = ("3D animated feature film still, Pixar and DreamWorks quality CG animation, stylized cartoon "
             "proportions, big expressive animated eyes, soft fur shading with subsurface glow, appealing rounded "
             "shapes, warm cinematic lighting, soft global illumination, saturated warm desert palette of "
             "terracotta, gold and turquoise, shallow depth of field, clean and polished, no humans, no text.")
STYLE_NIGHT = ("3D animated feature film still, Pixar and DreamWorks quality CG animation, stylized cartoon "
               "proportions, big expressive animated eyes, soft fur shading with subsurface glow, appealing rounded "
               "shapes, moonlit deep blue night with warm amber lantern light, soft volumetric mist, soft global "
               "illumination, shallow depth of field, clean and polished, no humans, no text.")

# Night frames where the hunter's lantern must NOT appear: "warm amber lantern light" in STYLE_NIGHT drew a lantern
# standing on the ground in 9/9 bear/away frames (2026-11-01 12:25 AM).
STYLE_NIGHT_NOLAMP = STYLE_NIGHT.replace("moonlit deep blue night with warm amber lantern light",
                                         "moonlit deep blue night, cold silver moonlight")

# For frames with NO character in them: the character words above ("big expressive animated eyes", "fur")
# make Z-Image invent a cute creature in an empty set (seen on every set candidate 2026-10-31 11:29 PM).
STYLE_SET_DAY = ("3D animated feature film still, Pixar and DreamWorks quality CG animation environment, stylized "
                 "appealing shapes, warm cinematic lighting, soft global illumination, saturated warm desert palette "
                 "of terracotta, gold and turquoise, clean and polished, empty of characters and creatures, no "
                 "humans, no animals, no text.")
STYLE_SET_NIGHT = ("3D animated feature film still, Pixar and DreamWorks quality CG animation environment, stylized "
                   "appealing shapes, moonlit deep blue night with warm amber lantern light, soft volumetric mist, "
                   "soft global illumination, clean and polished, empty of characters and creatures, no humans, no "
                   "animals, no text.")

CHAR = {
    "doug": ("Doug, a lanky long-legged tan-and-russet-red bloodhound with a long narrow head, very long droopy velvet "
             "ears that hang below his jaw, heavy saggy skin folds and deep wrinkles over his forehead and cheeks, droopy "
             "lower eyelids, long loose jowls, a big shiny black nose, soulful amber animated eyes "
             "under heavy brows, and a worn scarred dark-brown leather hunting collar with a dented brass ring"),
    "hank": ("Hank, a huge round gentle brown grizzly bear with thick dark chocolate-brown fur, a lighter tan muzzle, "
             "small round ears, kind dark-brown eyes, a big soft belly and enormous padded paws"),
    "rabbit": ("a lean desert jackrabbit with enormous tall pink-lined ears, sandy grey-brown fur, a white belly "
               "and long hind feet"),
    "hawk": ("a red-tailed hawk with rust-red tail feathers, a cream speckled chest, brown wings and a sharp "
             "hooked yellow beak"),
    "prairie": "a chubby tan prairie dog with tiny dark paws, round cheeks and bright black eyes",
    "monkey": ("a small brown capuchin monkey train conductor with a cream face, wearing a little navy-blue "
               "conductor's cap and a navy vest with brass buttons"),
    "giraffe": ("two tall friendly reticulated giraffes with orange-brown patch patterns, short ossicone horns "
                "and long eyelashes"),
    "elephant": ("a big friendly grey African elephant with huge flapping ears and a curled trunk, an oak water "
                 "barrel with brass hoops strapped to its side by a leather harness with a canvas hose"),
    "team": ("a harnessed team pulling in pairs, two chestnut horses in front, two tan one-humped camels in the "
             "middle and two black-and-white dairy cows nearest the wagon, all in brown leather harness"),
    "ant": ("a tiny red ant hero with big round shiny black eyes, curious antennae and six thin legs, wearing a "
            "small dented steel plate strapped to its back like armor with tiny leather straps"),
}
SET = {
    "wagon": ("a big red-and-gold wooden fire-wagon on four huge spoked wooden wheels with iron rims and brass "
              "hubs, brass bells and fittings, oak water barrels with brass hoops, coiled canvas hoses and a "
              "wooden driver's bench up front, never a truck, no tires"),
    "train": ("a colorful vintage circus steam train, a red-and-gold locomotive with a tall black smokestack and a "
              "brass whistle, followed by striped circus cars in red, yellow and blue with gold trim"),
    "forest": ("a night forest of tall dark pines and ferns, moonbeams through low mist, a winding dirt trail, "
               "a fallen mossy log and a muddy ditch with tangled roots"),
    "desert": ("a red-rock desert with distant mesas and buttes, golden sand, sagebrush and saguaro cactus, "
               "a single railroad track across the sand"),
    "canyon": ("the rim of a deep red-rock canyon, the railroad track running to the very edge and ending in "
               "mid-air at the rim, the far rim across the gap where the track continues"),
}

def p(style, *parts):
    return style + " " + " ".join(parts)
