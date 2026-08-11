import fs from "node:fs/promises";
import { PresentationFile } from "@oai/artifact-tool";

async function saveBlob(blob, path) {
  await fs.writeFile(path, Buffer.from(await blob.arrayBuffer()));
}

const imported = await PresentationFile.importPptx("scratch/probe_shapes.pptx");
console.log(imported.constructor.name, imported.slides.count);
await saveBlob(await imported.export({ slide: imported.slides.getItem(0), format: "png" }), "scratch/probe_import.png");
