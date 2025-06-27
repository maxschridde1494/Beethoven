import { useEffect } from "react";
import { OpenSheetMusicDisplay } from "opensheetmusicdisplay";

export function Score({ xml }: { xml: string }) {
  useEffect(() => {
    const osmd = new OpenSheetMusicDisplay("score", { autoResize: true });
    osmd
      .load(xml)   // <- no WS needed
      .then(() => osmd.render());
  }, []);

  return <div id="score" style={{ width: "100%" }} />;
}