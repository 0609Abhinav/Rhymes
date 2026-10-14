import os
import cv2
from rembg import new_session
from build_local_animated_video import SCENES, KEYFRAMES, find_image, make_scene
out=os.path.join(os.path.dirname(__file__),'rigged_backgrounds')
os.makedirs(out,exist_ok=True)
session=new_session('u2netp',providers=['CPUExecutionProvider'])
for i,(pattern,entities) in enumerate(SCENES,1):
    dst=os.path.join(out,f'scene_{i:02d}.png')
    if os.path.isfile(dst):
        print(f'keep {dst}'); continue
    print(f'inpainting illustration {i}/10: {pattern}',flush=True)
    scene=make_scene(pattern,entities,session)
    cv2.imwrite(dst,scene['background'],[cv2.IMWRITE_PNG_COMPRESSION,2])
print('Background plates ready:',out)
