const {
  Presentation,
  PresentationFile,
  column,
  text,
  fill,
  hug,
} = await import("@oai/artifact-tool");

const p = Presentation.create({ slideSize: { width: 1920, height: 1080 } });
const slide = p.slides.add();
slide.compose(
  column(
    { name: "root", width: fill, height: fill, padding: 96, gap: 24 },
    [
      text("Prueba GourmetPOS", {
        name: "title",
        width: fill,
        height: hug,
        style: { fontSize: 72, bold: true, color: "#111827" },
      }),
      text("Render de validacion", {
        name: "subtitle",
        width: fill,
        height: hug,
        style: { fontSize: 32, color: "#4B5563" },
      }),
    ],
  ),
  { frame: { left: 0, top: 0, width: 1920, height: 1080 }, baseUnit: 8 },
);

await (await PresentationFile.exportPptx(p)).save("scratch/probe.pptx");
for (const format of ["png", "layout", "pdf"]) {
  try {
    const blob = await p.export({ slide, format });
    await blob.save(`scratch/probe.${format === "layout" ? "json" : format}`);
    console.log(`ok ${format}`);
  } catch (err) {
    console.log(`fail ${format}: ${err?.message || err}`);
  }
}
