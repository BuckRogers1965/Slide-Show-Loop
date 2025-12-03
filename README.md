# Slide-Show-Loop

A compact, heuristic tool that organizes a chaotic collection of images into a coherent, dreamy video loop.   It ignores filenames and metadata, instead sorting images based purely on raw pixel similarity. This create fluid, dream-like visual morphs that compress surprisingly well in video streams.

The script attempts to make the loop return to the begining to make seamless looping animations.

## Requirements

1.  **Python 3.x**
2.  **Python Libraries:**
    ```bash
    pip install numpy opencv-python
    ```
3.  **FFmpeg:**
    *   Must be installed and accessible via your system's command line (PATH).

## Usage

Run the script pointing to a directory containing your images (`.jpg`, `.png`, `.bmp`).

```bash
python SlideShowLoop.py --fps 1 <path to directory with images>
```

### Arguments
*   `directory`: The folder containing the shuffled frames.
*   `--fps`: (Default: 24) The framerate for the base video. **Using `--fps 1` is recommended** if you intend to use the morphing filter; it gives the interpolator distinct "key frames" to blend between.
*   `--output`: (Default: `reassembled_movie.mp4`) The filename for the sorted verification video.

### The Output Process
The script performs two actions:

1.  **Automatic Sort:** It generates `reassembled_list.txt` and compiles a standard cut video (`reassembled_movie.mp4`) to verify the order.
2.  **The Morph Command:** Upon completion, the script **prints a complex FFmpeg command to the console**. You must copy and run this command manually to generate the final "dreamy" video. It uses the `minterpolate` filter to hallucinate motion between the sorted frames.
3. The script also prints a more standard slide show that does not morph between frames at much higher speeds. 

---

## How It Works: The "Good Enough" Philosophy

This script is built on the philosophy of **Heuristic Engineering**. It rejects mathematical perfection (finding the global optimum) in favor of perceptual validity (does it look right?). 

We utilize several aggressive tradeoffs to achieve high performance and specific aesthetic results:

### 1. Greedy Nearest-Neighbor Sorting
Finding the "perfect" order for a set of images is a variation of the *Traveling Salesman Problem* (NP-Hard). Calculating it perfectly would take eons.
*   **The Tradeoff:** We use a "Greedy" algorithm. The script picks a frame, looks for the best match available *right now*, and moves on.
*   **The Result:** It may hit local dead-ends, but visually, it preserves the "flow" of time. It reconstructs the arrow of time purely through visual similarity.

### 2. Aggressive Dimensionality Reduction
Comparing 4K images pixel-by-pixel is slow and prone to noise (grain, compression artifacts).
*   **The Tradeoff:** The script crushes every image down to a **64x64 grayscale** matrix.
*   **The Result:** This acts as a blur filter. It ignores high-frequency noise and focuses only on the composition and light intensity. This makes the sort incredibly fast and surprisingly more robust than a high-res comparison.

### 3. The "Early Exit" Optimization
The script uses a Mean Squared Error (MSE) threshold.
*   **The Tradeoff:** If it finds a frame that is "close enough" (MSE < 1000), it stops searching immediately. It doesn't care if there is a *slightly better* match later in the pile.
*   **The Result:** A massive speed boost. We assume that if two frames are that similar, they are sequential, allowing the algorithm to sprint through easy sections of the dataset.

### 4. Algorithmic Aesthetic & Compression
The visual style of the final video is a byproduct of the math:
*   **The "Dreamy" Look:** Because the images are sorted by pixel similarity, the FFmpeg `minterpolate` filter can easily generate "optical flow" vectors between them. It morphs one frame into the next, creating a liquid, hallucinogenic effect where distinct subjects seem to transform into one another.
*   **Compression Efficiency:** By sorting for minimal pixel change between frames, we drastically reduce the entropy of the video stream. The video encoder (H.264/H.265) can use inter-frame compression efficiently, resulting in high-motion video files that are barely larger than the original static slideshow.

