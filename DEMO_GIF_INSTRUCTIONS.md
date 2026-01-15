# Demo GIF Instructions

To complete the demo landing page, you need to add a `demo.gif` file to the root directory.

## How to Create the Demo GIF

### Option 1: Using a Screen Recorder
1. Open the demo page: https://jan-code26.github.io/glitchgetaway/
2. Use a screen recording tool like:
   - **LICEcap** (Windows/Mac) - https://www.cockos.com/licecap/
   - **Peek** (Linux) - https://github.com/phw/peek
   - **ScreenToGif** (Windows) - https://www.screentogif.com/
3. Record the following actions:
   - Show the landing page
   - Type an answer in the terminal
   - Press Enter
   - Show the success message
4. Save the recording as `demo.gif` (max 10MB for GitHub)
5. Optimize the GIF if needed using tools like:
   - **gifsicle**: `gifsicle -O3 --lossy=80 -o demo.gif demo-original.gif`
   - Online: https://ezgif.com/optimize

### Option 2: Using Screenshots + ImageMagick
1. Take sequential screenshots of the demo
2. Use ImageMagick to combine them:
   ```bash
   convert -delay 100 -loop 0 screenshot*.png demo.gif
   ```

### Recommended Settings
- Resolution: 800x600 or 1024x768
- Duration: 5-10 seconds
- File size: < 5MB
- Show: Landing page → Type answer → Success message

## Current Status
The landing page is complete and functional. The demo.gif placeholder will show 
"🎮 Gameplay demo coming soon!" until the actual GIF is added.

Once you have the GIF, simply place it in the root directory as `demo.gif`.
