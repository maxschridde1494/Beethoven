# Beethoven

*Beethoven may have been deaf, but this project “hears” a piano through sight – turning visual cues into music.*

## Introduction

**Beethoven** is a computer vision project that analyzes video of a piano keyboard to identify which keys are being pressed, effectively transcribing music without any audio input. It uses AI models to first determine the **relative positions of the piano keys** in the camera view, and then to **detect pressed keys (white or black)** in real-time. In homage to the composer Beethoven – who continued to create music after losing his hearing – this system doesn’t need ears to recognize a melody. Instead, it “listens” with its eyes, watching the keys and predicting the notes being played.

At its core, Beethoven leverages **Roboflow** object-detection models to run inference on video frames. Two models are used: one model calibrates the layout of the keyboard (finding all keys in the frame), and another model identifies when keys are pressed. By combining these, the system can map physical key presses to specific piano notes. The application is built with a modern web tech stack: a Python **FastAPI** server (for running inference and coordinating data) and a React frontend (for live visualization). These components communicate via WebSockets to stream detection results instantly to the browser. The entire setup runs in Docker containers for easy deployment and consistency across environments.

## Setup and Requirements

To get started with Beethoven on a local machine, make sure you have the following prerequisites:

* **Docker Desktop or Docker Engine** – The project is containerized using Docker Compose (Compose file format **3.9**), so you’ll need Docker to build and run the services.
* **Roboflow Account & API Key** – You must have a Roboflow inference API key to use the cloud-hosted models (or credentials for a self-hosted Roboflow inference server). The `.env.sample` file includes a placeholder for `ROBOFLOW_API_KEY` that you will need to fill in.
* **Piano Video Source** – One or more video feeds of the piano you want to analyze. This can be a **local video file** (e.g. an MP4 of a piano being played) or a **live RTSP stream** from a camera pointed at the piano. For each video source, you should also have a **static reference image** (a representative video frame) showing the piano keyboard at rest, which the system will use for initial calibration of key positions.

### Installation and Running (Development)

Follow these steps to set up and run Beethoven locally:

1. **Clone the Repository:** Get the code onto your machine. For example: `git clone https://github.com/yourusername/Beethoven.git` (replace with the correct URL). Then `cd Beethoven`.

2. **Create your Environment Config:** Copy the example environment file and adjust settings.

   * Duplicate **`.env.sample`** to a new file named **`.env`**, which Docker will use for configuration.

   * Open `.env` in an editor and fill in the required values. At minimum, set your Roboflow API key: `ROBOFLOW_API_KEY=<your_key_here>`. By default, the Roboflow API URL points to the cloud inference server (`https://detect.roboflow.com`), which you can leave as is for cloud inference or change to a local server address if you are running one (see **Roboflow Configuration** below).

   * Provide the details of your video stream(s) in `CAM_PROXY_CONFIG`. This variable is a JSON array of camera configs. For example, for a local video file you might use:

     ```json
     CAM_PROXY_CONFIG=[
       {
         "name": "middle-left",
         "stream_url": "app/assets/middle-left.mp4",
         "relative-position-img-path": "app/assets/middle-left-static.jpg"
       }
     ]
     ```

     In this example, “middle-left” is an arbitrary name for the camera/view (it will be used as an identifier), the `stream_url` points to a video file within the container (here a file mounted at `server/app/assets/middle-left.mp4`), and `relative-position-img-path` points to a static image file for that view. **Important:** Make sure the paths correspond to actual files. You should place your video files and initial images in the `server/app/assets/` directory (or adjust paths accordingly). If you have multiple camera views or videos, add multiple objects to the array and ensure each has a unique `name`.

   * Leave or adjust other settings as needed (see **Configuration** below for details on each variable). For now, note that by default the database URL is set to use the included Postgres container (`postgresql+psycopg2://postgres:postgres@db:5432/beethoven`) and `DATABASE_PERSIST_DETECTIONS=false` (meaning detection results won’t be saved to the DB unless you enable this).

3. **(Optional) Configure Media Stream Proxy:** By default, the Docker Compose setup uses **MediaMTX** (an RTSP/HLS server) with the provided config file **`server/mediamtx.yml`**. This file is already set up to work with the sample camera names “middle-left” and “edge-left,” expecting the server to publish those streams via FFmpeg. If you used those names in `CAM_PROXY_CONFIG` and are streaming local video files, you **do not need to change anything** in `mediamtx.yml` – the server will push the video to MediaMTX, which in turn will serve it for the web client.

   If, however, you plan to use **RTSP camera streams** directly, you might want MediaMTX to pull from those streams. In that case, edit `server/mediamtx.yml` and under the `paths:` section add your camera stream URLs. For example:

   ```yaml
   paths:
     mypiano:
       source: rtsp://<camera_username>:<password>@<camera_ip>:554/stream1
   ```

   This would tell MediaMTX to connect to an RTSP camera feed named “mypiano” (make sure the `name` in your `CAM_PROXY_CONFIG` is also "mypiano" in this case). The config file includes commented examples illustrating how to set up direct RTSP sources. For most local development use cases with video files, you can skip this step and use the default config (which waits for the server to publish streams).

4. **Launch the Application:** Start up the Docker containers using **Docker Compose**. Run:

   ```bash
   docker-compose up --build
   ```

   The first time, Docker will build the images for the server and client. Then it will start all services defined in the `docker-compose.yml` – this includes the backend server, frontend client, stream proxy, and database. You should see logs indicating each service is up. (You can add the `-d` flag to run in detached mode.)

5. **Access the Web Interface:** Once all services are running, open your browser to **`http://localhost:5173`**. This is the React client’s development server. The Beethoven UI should load, showing the configured video stream(s). For each video, you’ll see the live feed (via HLS) and an overlay of detection boxes. Initially, the system performs a one-time **calibration inference** on the provided static image(s) to identify all the keys in view. These **initial key positions** may be displayed (e.g. outlining keys) to show how the model sees the keyboard. As the video plays, any time a key press is detected, the corresponding key area will be highlighted with a bounding box (with labels or color indicating a white vs. black key press) in real-time.

6. **Using the System:** Play the video or observe the live camera feed. The backend continuously grabs frames (at the specified interval) and sends them to Roboflow for inference. Detected key presses will stream to the frontend. You can open your browser’s console to see debug logs (the client prints connection status and may log detections). If you have multiple camera views configured, you’ll see multiple video players on the page side by side. Each one will have its own overlay for detections.

7. **Shut Down:** When you’re done, press **Ctrl+C** in the terminal to stop the Docker Compose session. All containers will stop. If you want to remove containers (and the default database volume), you can run `docker-compose down`. The Postgres database uses a named volume (`pgdata`) to persist data, so stopping and starting the app will keep any saved detections (unless you tear down the volume).

## Docker Compose Architecture

Beethoven’s environment is defined in `docker-compose.yml`, which orchestrates several services working together. Here’s an overview of each service and its role:

* **Server (Backend)** – This is the Python FastAPI application that performs the AI inference and coordinates everything. It’s defined as the **“server”** service in Docker Compose. The server container is built from the provided Dockerfile (using the `server-dev` stage) and runs Uvicorn (the ASGI server) to host the FastAPI app on port **8000**. Key functions of the server: it loads your configuration from the environment, spawns background FFmpeg processes to handle video streams, and calls out to the Roboflow API for each frame (or every Nth frame as configured) to get detection results. The server then emits those results to clients via a WebSocket endpoint. It also exposes a REST API for certain things (for example, it serves the static initialization images at `/api/assets/...` and may have routes to fetch stored detections). The server depends on the database and stream proxy services (ensuring they start first). In development, the server code is mounted as a volume so you can edit it on the fly and it will auto-reload (thanks to Uvicorn’s `--reload` flag).

* **Client (Frontend)** – This is the React application (built with Vite) that provides the user interface. In Docker Compose it’s the **“client”** service. The client container runs the dev server on port **5173** (and uses port 3036 for Vite’s HMR websocket). When you open the browser to `localhost:5173`, you’re hitting this container. The client UI shows a video player for each configured camera feed and draws overlays for detections. It uses **HLS (HTTP Live Streaming)** to play the video streams and connects to the backend’s WebSocket (`ws://localhost:8000/ws`) to receive real-time detection data. The video stream URL for a camera is of the form `http://localhost:8888/<cameraName>/index.m3u8`, which is served by the MediaMTX proxy. The client knows the names (like “middle-left”) from the config and constructs the HLS URL accordingly. Each video player uses the `hls.js` library to handle the stream and an overlay canvas to draw bounding boxes for predictions. Like the server, the client source code is mounted into the container for live editing during development (no need to rebuild the image for frontend code changes; just save and Vite will hot-reload).

* **Stream Proxy (MediaMTX)** – The **“stream-proxy”** service runs a MediaMTX server (using the official `bluenviron/mediamtx:latest` image). MediaMTX is an open-source RTSP server that we use here to broker video streams. It accepts incoming RTSP streams (from our server’s FFmpeg or directly from cameras) and makes them available as RTSP and HLS to any consumers (in this case, the web client). In the provided config (`mediamtx.yml`), HLS output is enabled on port **8888**, and a couple of stream names are predefined. For example, the config expects a stream published to the path “middle-left” (and similarly for “edge-left”). The Beethoven server, on startup, will use FFmpeg to **push any local video files** to these RTSP endpoints (e.g., it runs an FFmpeg process that reads `middle-left.mp4` and streams it to `rtsp://rtsp-proxy:8554/middle-left` inside the Docker network). MediaMTX receives that and simultaneously makes it available as an HLS stream at `http://localhost:8888/middle-left/index.m3u8` for the frontend. If instead you have MediaMTX configured to pull directly from an IP camera (using the `source:` directives), then MediaMTX itself fetches the stream and you still get HLS output. The server will in parallel open its own FFmpeg reader on the stream (either the local file or the RTSP URL) to run inference on the frames. The stream-proxy runs in the background and typically needs no direct interaction – it starts automatically and restarts if any failure occurs (configured with `restart: unless-stopped` in Compose). The MediaMTX admin console is not exposed by default here; we simply use it as a headless relay.

* **Database (PostgreSQL)** – The **“db”** service is a PostgreSQL 17 database container. It stores inference results and any other data the server might need to persist. The compose file sets it up with a default database name (`beethoven`) and credentials (username/password: `postgres`/`postgres`). These credentials correspond to the `DATABASE_URL` in the `.env` (already set to use the service hostname `db` on port 5432). In practice, the database is mainly used if you enable data persistence for detections. When `DATABASE_PERSIST_DETECTIONS` is `true`, each detection event (each time the model finds pressed keys) will be saved as a record in the DB. This can be useful for later analysis, debugging, or building a history of what was played. If you leave it `false` (the default), the server will not write detections to the database, and you can even run the system with the database turned off (though the container will still be running, idle). The database’s data directory is stored in a Docker volume named **`pgdata`** so that data persists across restarts. If you ever need to reset the database to a clean state, you can stop the app and run `docker-compose down -v` to remove volumes (warning: that will delete recorded data).

* **(Optional) PGAdmin** – For convenience in development or debugging, the compose file includes a **pgAdmin 4** service definition (commented out by default). pgAdmin is a web GUI for PostgreSQL. If you want to use it, you can uncomment those lines and run compose. It will be available on port 8080 (URL: [http://localhost:8080](http://localhost:8080)) with a default login of `admin@example.com` / `postgres`. pgAdmin is not required for Beethoven to function – it’s just there if you want to inspect the database contents (e.g. to verify that detections are being saved).

## Configuration Details

Beethoven offers flexible configuration through environment variables (set in your `.env` file) and the MediaMTX YAML. Below is an overview of important configuration options and how to use them:

* **Roboflow API Configuration:** These settings tell the server how to reach the Roboflow inference service and which models to use. In the `.env`:

  * `ROBOFLOW_API_URL` – The URL of the Roboflow inference server. By default this is `https://detect.roboflow.com` (Roboflow’s cloud endpoint). If you are using Roboflow’s hosted service, keep this unchanged. If you have set up a **local Roboflow inference server** (for example, via a Docker container or on-premise service), you would change this to that server’s address. The comment in the sample file suggests `http://host.docker.internal:9001` as an example for a local server (assuming you run the Roboflow container on your host at port 9001; `host.docker.internal` allows the container to reach your host machine).
  * `ROBOFLOW_API_KEY` – Your private API key for Roboflow. This **must** be provided for authentication when using the cloud API (and may also be needed for a local server depending on how Roboflow’s local inference is set up). The key is usually a short string of letters/numbers you get from your Roboflow account dashboard. Keep this secret and do not commit it to source control.
  * `ROBOFLOW_MODEL_ID` – The identifier of the Roboflow **model used for main inference**, i.e. detecting pressed keys. It typically includes your workspace or project name and the model version number. In the sample it’s set to `"beethoven-keys-pressed/22"` (which implies a model named “Beethoven Keys Pressed”, version 22). You should set this to the model ID that detects **key presses** in your project.
  * `ROBOFLOW_RELATIVE_POSITION_MODEL_ID` – The identifier of the Roboflow **relative position model** that is used to find the piano keys’ positions. In the sample it’s `beethoven-relative-position/5`, corresponding to a model trained to detect the location of each piano key (distinguishing white vs black keys) on an image of a piano. This is run on the static reference image(s) once at startup for calibration. If you have your own model for this or if the ID is different in your Roboflow account, update this accordingly. If you choose not to perform an initial layout inference, you can leave this blank, and the server will skip the initial step (though skipping it means the system won’t know which specific keys are where, which could limit functionality).

* **Camera Stream Settings:** The `CAM_PROXY_CONFIG` variable in the environment config defines what video streams to use and how to initialize them. This is one of the most important configurations to get right. It is a JSON array of objects, where each object has:

  * `name` – A short identifier for the camera or video feed. Choose a simple name (no spaces) as it will be used in URLs and references. For example: `"middle-left"` or `"camera1"`. This name should correspond to an entry in the MediaMTX config so that an HLS stream is available for it. In the default `mediamtx.yml`, **“middle-left”** and **“edge-left”** are pre-defined. If you use different names, you should modify `mediamtx.yml` accordingly (or add the new names).

  * `stream_url` – The location of the video source. This can be a file path or a network stream URL. If the value does **not** start with `rtsp://`, the system assumes it’s a local file path. For example, `"app/assets/middle-left.mp4"` would refer to a video file (mounted in the server container). The server will launch FFmpeg to read this file and **publish** it to the stream proxy (MediaMTX) under the given `name`. It will also loop the video continuously (`-stream_loop -1` in FFmpeg) so the stream acts like a live source. If the value **does** start with `rtsp://`, the server treats it as a live RTSP feed (e.g., from an IP camera). In that case, the server will directly connect to that RTSP URL for analysis, and it expects that the stream proxy will also have that feed available for the client. You can achieve that either by having the server itself push the RTSP into MediaMTX (the server isn’t currently set up to re-stream RTSP to RTSP, it usually pushes file sources) or by configuring MediaMTX to pull the camera’s RTSP feed as described earlier. In summary: use file paths for local videos or use `rtsp://` URLs for live streams, and ensure MediaMTX is aware of those streams (for files, it’s automatic; for direct RTSP, configure mediamtx or adapt as needed).

  * `relative-position-img-path` – Path to the static image file used for initial inference for that camera. For best results, this image should be a clear shot of the piano keys (from the same angle as the video) without hands or motion – essentially what the piano looks like at rest. The server will load this image at startup and run the `ROBOFLOW_RELATIVE_POSITION_MODEL_ID` detection on it to identify all the keys and their positions. From that, it can map out which key is which (e.g., “this bounding box corresponds to note C4, key number 40”, etc.). The path can be relative to the `server/app` directory (like in the sample, which assumes images are in `app/assets/`). **Tip:** name your image file something like `<cameraName>-static.jpg` to keep it clear (the sample code actually tries to fetch `<name>-static.jpg` from the API static files route). After adding your images, you might need to adjust `server/app/main.py` to mount the `assets` folder for static serving if it isn’t already (in case you want to serve images through the API).

  * **Frame Interval:** Another related setting is `INTERVAL`, which controls how often frames are sampled from the video for inference. By default `INTERVAL=1` (which effectively means every frame, if 1 is interpreted as one frame interval). You can increase this number to process frames less frequently (e.g., `2` to take every other frame, or a fractional value like `0.5` to process two frames per second if your video is 1 FPS, depending on implementation). The interval is in seconds between inference runs in the code, so if your video is 30 FPS and you set `INTERVAL=1`, it might infer roughly every second, not every frame – be mindful of how it’s implemented if you adjust it. Tuning this can help with performance if needed.

* **Database Settings:** In most cases you won’t need to change the database config for local use. The provided `DATABASE_URL` will point the server to the included Postgres container. However, if you want to connect to an external or existing Postgres instance, you can change this URL accordingly (just be sure the container can reach it, and adjust credentials). The format is `postgresql+psycopg2://username:password@host:port/dbname`. The variables `POSTGRES_USER`, `POSTGRES_PASSWORD`, etc., in the docker-compose are for initializing the internal DB and typically don’t need changing. The main toggles you have are:

  * `DATABASE_PERSIST_DETECTIONS` – set this to `"true"` if you want to save detection events to the database. Each detection (each frame where the model finds one or more pressed keys) will be inserted into a table, along with info like timestamp, which key, confidence, etc. This can generate a lot of data over time, so if you’re just testing or don’t need that record, leave it as `"false"`. Even with it false, the database can still be used by other features, but currently its primary use is storing detections.
  * `DATABASE_ECHO` – set this to `"true"` to enable SQL query logging from SQLAlchemy (the ORM). This is mainly for debugging; it will print SQL statements to the server log. It’s safe to leave false unless you are diagnosing a database issue or want to see the exact queries being run.

* **Logging Level:** You can control the verbosity of the server logs with the `LOG_LEVEL` variable. By default it’s `INFO`, which prints informational messages, key events, and warnings/errors. If you need more detail (for example, debugging why something isn’t working), you can set `LOG_LEVEL=DEBUG` to get very detailed logs. Conversely, you could set it to `WARNING` or `ERROR` to reduce output. The server’s logging is configured via a custom logger utility and will respect this level across the app.

* **MediaMTX Config:** While not an environment variable, it’s worth noting the role of **`server/mediamtx.yml`** in configuration. This file defines how the MediaMTX (stream proxy) operates. We’ve discussed it above, but to recap: the config included in the repo enables HLS streaming and sets up placeholder stream names expecting a publisher. If you add or change camera `name`s, update this file to have corresponding entries under `paths:`. If you want to ingest RTSP streams directly, put them here as `source` URLs (and comment out or remove the `source: publisher` entries for those names). The container automatically loads this config on startup (the compose file mounts it read-only into the container). Typically you won’t need to change `mediamtx.yml` for initial testing with the default names – just ensure your `CAM_PROXY_CONFIG` names match those in the config.

## Roadmap

Beethoven is a work in progress with ambitious goals. Here are a couple of key features on the roadmap that will make the system even more powerful and musical:

* **Automatic Transcription to Sheet Music:** *Turning a series of key presses into written music, Beethoven-style.* With the ability to identify notes and the timing of each press, the project aims to generate a musical score from the video. Essentially, as the system “listens” to the pianist by watching the keys, it will record the sequence of notes and durations, then compile them into a readable format (such as a MIDI file or even rendered sheet music). This would allow someone to record themselves playing the piano (on video) and get back a transcription of what they played – all without any microphone. Achieving this will require tracking the timing between key press events (to determine rhythm and note length) and grouping notes into measures, applying music theory rules for notation. It’s an ambitious feature, but fitting – Beethoven the AI could write out music the way Beethoven the composer might have, without ever hearing a sound.

---

With these components in place, Beethoven provides a novel way to **“hear” music through images**. From setting up cameras and containers to processing predictions in real-time, the project brings together computer vision, orchestration, and a bit of musical theory. We hope you find it useful or inspiring – and remember, even if you can’t hear the melody, the eyes and AI of Beethoven are here to help translate those piano performances into notes and lines. Enjoy making music visible!
