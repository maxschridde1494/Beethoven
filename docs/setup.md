## Setup and Requirements

To get started with Beethoven on a local machine, make sure you have the following prerequisites:

* **Docker Desktop or Docker Engine** – The project is containerized using Docker Compose (Compose file format **3.9**), so you'll need Docker to build and run the services.
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

     In this example, "middle-left" is an arbitrary name for the camera/view (it will be used as an identifier), the `stream_url` points to a video file within the container (here a file mounted at `server/app/assets/middle-left.mp4`), and `relative-position-img-path` points to a static image file for that view. **Important:** Make sure the paths correspond to actual files. You should place your video files and initial images in the `server/app/assets/` directory (or adjust paths accordingly). If you have multiple camera views or videos, add multiple objects to the array and ensure each has a unique `name`.

   * Leave or adjust other settings as needed (see **Configuration** below for details on each variable). For now, note that by default the database URL is set to use the included Postgres container (`postgresql+psycopg2://postgres:postgres@db:5432/beethoven`) and `DATABASE_PERSIST_DETECTIONS=false` (meaning detection results won't be saved to the DB unless you enable this).

3. **(Optional) Configure Media Stream Proxy:** By default, the Docker Compose setup uses **MediaMTX** (an RTSP/HLS server) with the provided config file **`server/mediamtx.yml`**. This file is already set up to work with the sample camera names "middle-left" and "edge-left," expecting the server to publish those streams via FFmpeg. If you used those names in `CAM_PROXY_CONFIG` and are streaming local video files, you **do not need to change anything** in `mediamtx.yml` – the server will push the video to MediaMTX, which in turn will serve it for the web client.

   If, however, you plan to use **RTSP camera streams** directly, you might want MediaMTX to pull from those streams. In that case, edit `server/mediamtx.yml` and under the `paths:` section add your camera stream URLs. For example:

   ```yaml
   paths:
     mypiano:
       source: rtsp://<camera_username>:<password>@<camera_ip>:554/stream1
   ```

   This would tell MediaMTX to connect to an RTSP camera feed named "mypiano" (make sure the `name` in your `CAM_PROXY_CONFIG` is also "mypiano" in this case). The config file includes commented examples illustrating how to set up direct RTSP sources. For most local development use cases with video files, you can skip this step and use the default config (which waits for the server to publish streams).

4. **Launch the Application:** Start up the Docker containers using **Docker Compose**. Run:

   ```bash
   docker-compose up --build
   ```

   The first time, Docker will build the images for the server and client. Then it will start all services defined in the `docker-compose.yml` – this includes the backend server, frontend client, stream proxy, and database. You should see logs indicating each service is up. (You can add the `-d` flag to run in detached mode.)

5. **Access the Web Interface:** Once all services are running, open your browser to **`http://localhost:5173`**. This is the React client's development server. The Beethoven UI should load, showing the configured video stream(s). For each video, you'll see the live feed (via HLS) and an overlay of detection boxes. Initially, the system performs a one-time **calibration inference** on the provided static image(s) to identify all the keys in view. These **initial key positions** may be displayed (e.g. outlining keys) to show how the model sees the keyboard. As the video plays, any time a key press is detected, the corresponding key area will be highlighted with a bounding box (with labels or color indicating a white vs. black key press) in real-time.

6. **Using the System:** Play the video or observe the live camera feed. The backend continuously grabs frames (at the specified interval) and sends them to Roboflow for inference. Detected key presses will stream to the frontend. You can open your browser's console to see debug logs (the client prints connection status and may log detections). If you have multiple camera views configured, you'll see multiple video players on the page side by side. Each one will have its own overlay for detections.

7. **Shut Down:** When you're done, press **Ctrl+C** in the terminal to stop the Docker Compose session. All containers will stop. If you want to remove containers (and the default database volume), you can run `docker-compose down`. The Postgres database uses a named volume (`pgdata`) to persist data, so stopping and starting the app will keep any saved detections (unless you tear down the volume). 