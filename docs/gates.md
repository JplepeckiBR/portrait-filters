# Gates: portrait filters

### G1 - Problem
*Is something actually blocked?*

- jplepecki.tech is a maker's desk drawn as physical objects. A plain phone photo of me breaks that: it has its own lighting and colour, so it looks pasted on, not printed.
- I want two portraits on the site that look like they were printed (a two-colour riso and copper dots on a circuit board), and I want to explain how they were made instead of hiding it behind an app filter.

`GATE: passed`

### G2 - What already exists
*Why not just use a tool?*

- Photoshop / Photopea halftone and riso presets, and dozens of web "riso effect" generators, produce the look.
- None of them let me explain every step, version it, or re-run it on new photos with the same settings. The point here is the explanation, so the code is the product.

`GATE: passed`

### G3 - Approaches

1. Apply a preset in an editor and export. Fast, unexplainable, not repeatable.
2. ML style transfer. Heavy, unpredictable, and teaches nothing about images.
3. **Chosen:** a small NumPy + Pillow pipeline: RGB to luma, kernels for sharpening and local contrast, then ordered dithering (riso) or cell-based dots (halftone). Every step is a few lines and can be shown in a post.

`GATE: passed`

### G4 - Project
*Smallest version that still answers the question.*

- Two filters (`riso`, `copper`), one CLI, example images, a blog post that walks through the kernels.
- **Done-test:** someone clones the repo, runs one command on their own photo, and gets an image that looks like the ones on jplepecki.tech.
- **Deliberately deferred:** a web demo, more inks, CMYK halftone angles, automatic background removal (use any cutout tool and pass a transparent PNG).

`GATE: passed`

### G5 - Steps and number

- Build the two filters, render examples, publish the repo and the post, put both portraits on the site linking to the post.
- **The one number:** clicks from the portraits to the post in the first month (Cloudflare or site analytics).
- **First task + time estimate:** the luma + convolution module, 30 minutes.

`GATE: passed`
