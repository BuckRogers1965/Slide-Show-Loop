import cv2
import os
import argparse
import numpy as np
import sys

# Increase recursion depth just in case
sys.setrecursionlimit(2000)

def get_image_files(directory):
    valid_extensions = ('.jpg', '.png', '.bmp')
    files = [os.path.join(directory, f) for f in os.listdir(directory) if f.lower().endswith(valid_extensions)]
    # Randomize initially so directory order doesn't bias the process
    import random
    random.shuffle(files) 
    return files

def load_small_grayscale(image_path):
    """
    Load image, convert to grayscale, and shrink it.
    We shrink it (e.g., 64x64) because comparing 4K frames 
    pixel-by-pixel would take too long.
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None: return None
    # resizing acts as a blur/hash to ignore grain noise
    return cv2.resize(img, (64, 64)).astype('float32')

def generate_ffmpeg_list(files, output_txt, fps):
    with open(output_txt, 'w') as f:
        # 1. BEGINNING: Write the first frame with duration 0
        # This sets the initial state for the morph filter without taking up time
        first_file = files[0]
        safe_first = first_file.replace("'", "'\\''")
        
        f.write(f"file '{safe_first}'\n")
        f.write(f"duration 0\n")

        # 2. MIDDLE: Write the rest of the chain (skipping the first one)
        # They get the standard duration
        for file_path in files[1:]:
            safe_path = file_path.replace("'", "'\\''")
            f.write(f"file '{safe_path}'\n")
            f.write(f"duration {1/fps}\n")

        # 3. END: Repeat the first frame with duration 0 
        # This tells the morph filter to transition back to the start
        f.write(f"file '{safe_first}'\n")
        f.write(f"duration 0\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", help="Folder with shuffled frames")
    parser.add_argument("--fps", type=float, default=24, help="Movie framerate")
    parser.add_argument("--output", default="reassembled_movie.mp4")
    args = parser.parse_args()
    
    raw_files = get_image_files(args.directory)
    print(f"--- Loading {len(raw_files)} shuffled frames into memory... ---")

    pool = {}
    for f in raw_files:
        data = load_small_grayscale(f)
        if data is not None:
            pool[f] = data

    # --- NEW: OUTLIER DETECTION ---
    print("--- Finding the 'Most Different' outlier to start the chain... ---")
    
    # 1. Calculate the 'Average Image' of the entire set
    if len(pool) > 0:
        all_imgs = np.array(list(pool.values()))
        mean_img = np.mean(all_imgs, axis=0)

        # 2. Find the image with the highest distance from the mean
        start_img_name = None
        max_dist = -1.0

        for name, data in pool.items():
            diff = np.sum((data - mean_img) ** 2)
            if diff > max_dist:
                max_dist = diff
                start_img_name = name

        print(f"Starting with outlier: {os.path.basename(start_img_name)}")
        
        # 3. Set that as the start of the chain
        current_img = start_img_name
        sorted_chain = [current_img]
        current_data = pool[current_img]
        del pool[current_img]
    else:
        print("No valid images found.")
        return

    print(f"--- Reassembling via Pixel Difference (MSE) ---")

    # While frames exist
    while pool:
        best_match_file = None
        # Initialize with infinity so the first check is always lower
        lowest_diff = float('inf') 
        
        for candidate_file, candidate_data in pool.items():
            # MSE: Mean Squared Error. 
            diff = np.sum((current_data - candidate_data) ** 2)
            
            if diff < lowest_diff:
                lowest_diff = diff
                best_match_file = candidate_file
                
                # OPTIMIZATION: If the frames are incredibly close, stop searching.
                if diff < 1000: 
                    break

        if best_match_file:
            if len(sorted_chain) % 50 == 0:
                print(f"Chained {len(sorted_chain)} frames...")
                
            current_img = best_match_file
            current_data = pool[best_match_file]
            sorted_chain.append(current_img)
            del pool[current_img]
        else:
            break

    txt_filename = "reassembled_list.txt"
    generate_ffmpeg_list(sorted_chain, txt_filename, args.fps)

    print(f"\nReassembly complete. {len(sorted_chain)} frames ordered.")
    
    cmd = (f"ffmpeg -f concat -safe 0 -i {txt_filename} "
           f"-r {args.fps} -pix_fmt yuv420p {args.output}")
    print(cmd)
    print()
    print("To blend in between the frames in a cpu heavy way (Seamless Loop):")
    # Using single quotes for python string so double quotes work inside for the filter
    print('ffmpeg -f concat -safe 0 -i reassembled_list.txt '
          '-vf "minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" '
          '-pix_fmt yuv420p morph_slideshow.mp4')

if __name__ == "__main__":
    main()