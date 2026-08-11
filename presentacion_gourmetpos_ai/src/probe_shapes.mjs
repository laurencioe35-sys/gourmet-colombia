import fs from "node:fs/promises";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

async function saveBlob(blob, path) {
  const buffer = Buffer.from(await blob.arrayBuffer());
  await fs.writeFile(path, buffer);
}

const p = Presentation.create({ slideSize: { width: 1920, height: 1080 } });
const slide = p.slides.add();

const bg = slide.shapes.add({
  geometry: "rect",
  position: { left: 0, top: 0, width: 1920, height: 1080 },
  fill: { type: "solid", color: "#101820" },
  line: { fill: { type: "none" } },
});
bg.name = "background";

const band = slide.shapes.add({
  geometry: "rect",
  position: { left: 120, top: 120, width: 1680, height: 200 },
  fill: { type: "solid", color: "#FF6B35" },
  line: { fill: { type: "none" } },
});
band.name = "accent-band";

const title = slide.shapes.add({
  geometry: "rect",
  position: { left: 150, top: 150, width: 1500, height: 130 },
  fill: { type: "solid", color: "#FF6B35" },
  line: { fill: { type: "none" } },
});
title.name = "title-box";
title.text.style = {
  fontSize: 54,
  bold: true,
  typeface: "Aptos Display",
  color: "#FFFFFF",
  verticalAlignment: "middle",
};
title.text = "Prueba de shape y texto editable";

await (await PresentationFile.exportPptx(p)).save("scratch/probe_shapes.pptx");
await saveBlob(await p.export({ slide, format: "png" }), "scratch/probe_shapes.png");
