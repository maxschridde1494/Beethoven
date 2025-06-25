import { useEffect } from "react";
import { OpenSheetMusicDisplay } from "opensheetmusicdisplay";
import { sampleXML } from "./sampleMusicxml";

export default function DemoScore() {
  useEffect(() => {
    const osmd = new OpenSheetMusicDisplay("score", { autoResize: true });
    osmd
      .load(sampleXML)   // <- no WS needed
      .then(() => osmd.render());
  }, []);

  return <div id="score" style={{ width: "100%" }} />;
}