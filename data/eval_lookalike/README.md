# Look-alike pairs (P1)

Real test pairs for `eval/lookalike_eval.py`: is it the **same load** photographed again (another angle,
another moment), or a **different load** in the same shop? Put the images in this folder (gitignored) and
list each pair in `pairs.csv`:

```
file_a,file_b,same_load,source
pet_a1.jpg,pet_a2.jpg,yes,nano-banana
pet_a1.jpg,pet_b1.jpg,no,nano-banana
sack1_front.jpg,sack1_side.jpg,yes,phone
```

Mark AI-made pairs `nano-banana` and phone pairs `phone`; they are scored together but the source is kept.

## Making same-load pairs with Nano Banana
Give it one of the Kaggle photos (e.g. `cg_01.png`) and ask for a second view of the same scene:

```
Show this exact same scene and the exact same load in the pan (the same bottles, the same sack,
the same items in the same arrangement), photographed again a few seconds later by the same
person from about 30 degrees to the [left/right] and slightly [higher/lower]. The scale, the pan
and everything in it must be the same objects. Natural phone photo, same light. Do not add,
remove or rearrange anything in the pan.
```

Check each output: if anything in the pan changed, it is not a same-load pair; discard it.
Aim for about 10 same-load pairs (left and right angles of 5 photos) and pair some of them with a
different load from the same shop for `no` rows. Five real phone pairs (one sack, two angles) make
the result much more convincing than any number of AI pairs.
