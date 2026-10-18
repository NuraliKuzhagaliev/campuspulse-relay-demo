import { api } from "./api";

/** Both Electron selection paths use JSON/base64, never multipart IPC. */
export async function importSelectedSource(file?: File): Promise<boolean> {
  if (window.relay) {
    let chosen;
    if (file) {
      if (
        !/\.(pdf|md|txt|ics)$/i.test(file.name) ||
        file.size <= 0 ||
        file.size > 10 * 1024 * 1024
      )
        throw new Error(
          "UNSUPPORTED_INPUT: Choose a supported file within 10 MiB.",
        );
      const bytes = new Uint8Array(await file.arrayBuffer());
      let binary = "";
      for (let offset = 0; offset < bytes.length; offset += 8192)
        binary += String.fromCharCode(...bytes.subarray(offset, offset + 8192));
      chosen = { name: file.name, content: btoa(binary) };
    } else chosen = await window.relay.importFile();
    if (!chosen) return false;
    await api("/import-native", "POST", chosen);
  } else if (file) {
    const form = new FormData();
    form.append("file", file);
    await api("/import", "POST", form);
  } else return false;
  return true;
}
