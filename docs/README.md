# docs

Place the demo recording here as **`demo.gif`** (referenced from the top-level
`README.md`).

## How to produce `demo.gif`

1. **Open the live dashboard** (`https://calib-frontend.onrender.com`). Give the
   free API ~30–60s to wake if it has gone idle.

2. **Start a screen recording** of just the dashboard area:
   - macOS: `Cmd+Shift+5` → *Record Selected Portion* → drag over the dashboard.
   - Save the `.mov` (QuickTime) when done.

3. **Drive the demo arc** (baseline → drift → alert → conformal recovery):

   ```bash
   ./scripts/demo_drive.sh                       # uses the Render deployment
   # or against a local stack:
   ./scripts/demo_drive.sh http://localhost:8000
   ```

   Runs ~35s. Stop the recording when it prints "Done".

4. **Convert the recording to a looping GIF.** With `ffmpeg` (best quality via a
   palette):

   ```bash
   ffmpeg -i recording.mov -vf "fps=12,scale=900:-1:flags=lanczos,palettegen" -y /tmp/pal.png
   ffmpeg -i recording.mov -i /tmp/pal.png -lavfi "fps=12,scale=900:-1:flags=lanczos,paletteuse" -y docs/demo.gif
   ```

   Or with [`gifski`](https://gif.ski) (`brew install gifski`) for smaller files:

   ```bash
   gifski --fps 12 --width 900 -o docs/demo.gif recording.mov
   ```

   Aim for < ~8 MB so it renders inline on GitHub.

5. Commit `docs/demo.gif`. The top-level README already references it.
