const $ = (id) => document.getElementById(id);
let currentVideoUrl = "";

function showStatus(message) {
  $("status").textContent = message || "";
}

async function readResponse(response) {
  const contentType = response.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "O servidor não conseguiu concluir.");
    return data;
  }

  const body = await response.text();
  if (!response.ok) {
    throw new Error("O servidor retornou uma página em vez dos dados esperados. Confira a configuração da hospedagem.");
  }
  throw new Error("Resposta inesperada do servidor. Confira se o projeto foi publicado corretamente.");
}

async function postJson(path, payload) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return readResponse(response);
}

$("paste-button").addEventListener("click", async () => {
  try {
    $("video-url").value = await navigator.clipboard.readText();
    showStatus("Link colado. Agora toque em carregar vídeo.");
  } catch {
    showStatus("Não consegui acessar a área de transferência. Cole o link manualmente.");
  }
});

$("load-button").addEventListener("click", async () => {
  const url = $("video-url").value.trim();
  if (!url) {
    showStatus("Cole um link do TikTok primeiro.");
    return;
  }

  const button = $("load-button");
  button.disabled = true;
  showStatus("Carregando vídeo...");
  $("result-card").classList.add("hidden");

  try {
    const data = await postJson("/api/info", { url });
    currentVideoUrl = url;

    $("video-title").textContent = data.title || "Vídeo do TikTok";
    $("video-description").textContent = data.description || "Sem descrição disponível.";
    $("video-author").textContent = data.author ? "Criador: " + data.author : "";

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
    showStatus("Vídeo carregado!");
  } catch (error) {
    showStatus(error.message || "Erro ao carregar o vídeo.");
  } finally {
    button.disabled = false;
  }
});

$("download-button").addEventListener("click", async () => {
  if (!currentVideoUrl) return;

  const button = $("download-button");
  button.disabled = true;
  showStatus("Preparando o download na melhor qualidade disponível...");

  try {
    const response = await fetch("/api/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: currentVideoUrl })
    });

    if (!response.ok) {
      await readResponse(response);
    }

    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = "download-free-videos.mp4";
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(objectUrl), 1500);
    showStatus("Download iniciado!");
  } catch (error) {
    showStatus(error.message || "Erro no download.");
  } finally {
    button.disabled = false;
  }
});
      
