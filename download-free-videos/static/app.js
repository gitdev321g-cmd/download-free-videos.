
const $ = id => document.getElementById(id);
let currentInput = "";

function status(message) {
  $("status").textContent = message || "";
}

async function post(path, data) {
  const response = await fetch(path, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(data)
  });

  const type = response.headers.get("content-type") || "";

  if (type.includes("application/json")) {
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Erro no servidor.");
    return result;
  }

  throw new Error("Resposta inválida do servidor. Confira o Render.");
}

$("paste-button").addEventListener("click", async () => {
  try {
    $("video-url").value = await navigator.clipboard.readText();
    status("Texto colado! Clique em carregar vídeo.");
  } catch {
    status("Cole o link manualmente.");
  }
});

$("load-button").addEventListener("click", async () => {
  const input = $("video-url").value.trim();

  if (!input) {
    status("Cole o link do TikTok!");
    return;
  }

  $("load-button").disabled = true;
  $("result-card").classList.add("hidden");
  status("Carregando vídeo...");

  try {
    const data = await post("/api/info", {url: input});
    currentInput = input;

    $("video-title").textContent = data.title || "Vídeo do TikTok";
    $("video-description").textContent =
      data.description || "Sem descrição disponível.";
    $("video-author").textContent =
      data.author ? "Criador: " + data.author : "";

    const video = $("video-preview");
    const image = $("video-thumbnail");
    const placeholder = $("preview-placeholder");

    video.pause();
    video.removeAttribute("src");
    video.load();

    image.removeAttribute("src");
    video.classList.add("hidden");
    image.classList.add("hidden");
    placeholder.classList.remove("hidden");

    if (data.preview_url) {
      video.src = data.preview_url;
      video.classList.remove("hidden");
      placeholder.classList.add("hidden");
      video.onerror = () => {
        video.classList.add("hidden");
        if (data.thumbnail) {
          image.src = data.thumbnail;
          image.classList.remove("hidden");
        } else {
          placeholder.classList.remove("hidden");
        }
      };
      video.load();
    } else if (data.thumbnail) {
      image.src = data.thumbnail;
      image.classList.remove("hidden");
      placeholder.classList.add("hidden");
    }

    $("result-card").classList.remove("hidden");
    status("Vídeo encontrado! Pode baixar.");
  } catch (error) {
    status(error.message);
  } finally {
    $("load-button").disabled = false;
  }
});

$("download-button").addEventListener("click", async () => {
  if (!currentInput) return;

  const button = $("download-button");
  button.disabled = true;
  status("Preparando download...");

  try {
    const response = await fetch("/api/download", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({url: currentInput})
    });

    if (!response.ok) {
      const result = await response.json();
      throw new Error(result.error || "Erro no download.");
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "download-free-videos.mp4";
    document.body.appendChild(link);
    link.click();
    link.remove();

    setTimeout(() => URL.revokeObjectURL(url), 1500);
    status("Download iniciado!");
  } catch (error) {
    status(error.message);
  } finally {
    button.disabled = false;
  }
});
