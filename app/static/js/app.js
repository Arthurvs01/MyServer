async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`Erro na requisição: ${response.status}`);
  }
  return response.json();
}

document.addEventListener("DOMContentLoaded", () => {
  console.log("CasaPy carregado");
});
