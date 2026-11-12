// medico — plugin opencode v2 (best-effort).
// Gerar com: sh Infra/skills/instalar.sh --hooks (escreve em hooks/gerados/),
// depois copiar o ficheiro gerado para ~/.config/opencode/plugins/medico.ts.
// /home/ai/.agents/skills/medico e python3 são materializados pelo instalador.
//
// Subscreve session.idle (fim de turno -> nudge do medico) e
// session.compacted (pos-compact -> snapshot atualizado).
// Falhas sao ignoradas de proposito: o medico nunca pode partir o opencode.
//
// v2: default export = { id, setup }. O helper $ do Bun saiu; spawn directo.
// Nunca concatenar SCRIPTS numa string de shell — spawn recebe argumentos.

import { spawn } from "node:child_process"

const PYTHON = "python3"
const SCRIPTS = "/home/ai/.agents/skills/medico/hooks/scripts"

function run(script: string, cwd: string): Promise<void> {
  return new Promise((resolve) => {
    try {
      const child = spawn(PYTHON, [script], { cwd, stdio: "ignore" })
      const done = () => resolve()
      child.on("error", done)
      child.on("close", done)
    } catch {
      resolve()
    }
  })
}

export default {
  id: "medico",
  setup(ctx: { event: { subscribe: (opts?: { signal?: AbortSignal }) => AsyncIterable<{ type: string; location?: { directory?: string } }> }; location?: { directory?: string } }) {
    const controller = new AbortController()
    const fallbackDir = ctx.location?.directory ?? process.cwd()

    void (async () => {
      try {
        for await (const event of ctx.event.subscribe({ signal: controller.signal })) {
          try {
            const cwd = event.location?.directory ?? fallbackDir
            if (event.type === "session.idle") {
              await run(`${SCRIPTS}/medico_stop_nudge.py`, cwd)
            }
            if (event.type === "session.compacted") {
              await run(`${SCRIPTS}/medico_precompact.py`, cwd)
            }
          } catch {
            // best-effort: nunca propagar
          }
        }
      } catch {
        // abort / stream fechado
      }
    })()

    return () => controller.abort()
  },
}
