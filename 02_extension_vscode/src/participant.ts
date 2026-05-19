/**
 * NTTDATA IBM TWX Copilot Chat Participant
 *
 * Usage in Copilot Chat:
 *   @nttdata v1.0 analyze  path/to/file.twx
 *   @nttdata v1.0 services path/to/file.twx
 *   @nttdata v1.0 flows    path/to/file.twx
 *   @nttdata v1.0 docs     path/to/file.twx
 *   @nttdata v1.0 entities path/to/file.twx
 *   @nttdata v1.0 scripts  path/to/file.twx
 *   @nttdata v1.0 endpoints path/to/file.twx
 *   @nttdata v1.0 deps     path/to/file.twx
 *   @nttdata v1.0 entries  path/to/file.twx
 *   @nttdata help
 */

import * as vscode from "vscode";
import { execFile } from "child_process";
import { promisify } from "util";
import * as path from "path";
import * as fs from "fs";

const execFileAsync = promisify(execFile);

const CORPORATE = "NTTDATA";
const SUITE_VERSION = "1.0.0";

// ASCII banner rendered in Copilot Chat (monospace markdown code block)
const NTTDATA_BANNER = `\`\`\`
   ╭──────╮   ███╗  ██╗ ████████╗████████╗  ██████╗  █████╗ ████████╗ █████╗
  ╱ ╭────╮ ╲  ████╗ ██║ ╚══██╔══╝╚══██╔══╝  ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗
 │  │  ◉  │ │ ██╔████╗██║    ██║      ██║   ██║  ██║███████║   ██║   ███████║
 │  ╰────╯  │ ██║╚═██╗██║    ██║      ██║   ██║  ██║██╔══██║   ██║   ██╔══██║
  ╲         ╱  ██║  ╚████║    ██║      ██║   ██████╔╝██║  ██║   ██║   ██║  ██║
   ╰──────╯   ╚═╝   ╚═══╝    ╚═╝      ╚═╝   ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝
\`\`\``;

const VALID_COMMANDS = [
    "analyze", "entities", "services", "flows",
    "deps", "docs", "scripts", "endpoints", "entries",
] as const;

type TWXCommand = typeof VALID_COMMANDS[number];

const COMMAND_DESCRIPTIONS: Record<TWXCommand, string> = {
    analyze:   "Resumen completo del paquete TWX",
    entities:  "Business Objects y modelos de datos",
    services:  "Servicios, pasos y lógica interna",
    flows:     "Diagramas de flujo Mermaid por proceso",
    deps:      "Grafo de dependencias entre artefactos",
    docs:      "Documentación Markdown completa",
    scripts:   "Scripts JavaScript/Groovy embebidos",
    endpoints: "Endpoints REST/SOAP externos",
    entries:   "Puntos de entrada (artefactos sin caller)",
};

export class NTTDATAParticipant {
    private readonly context: vscode.ExtensionContext;

    constructor(context: vscode.ExtensionContext) {
        this.context = context;
    }

    register(): void {
        const participant = vscode.chat.createChatParticipant(
            "nttdata.ibm-twx",
            this.handleRequest.bind(this),
        );
        participant.iconPath = vscode.Uri.joinPath(this.context.extensionUri, "icon.png");
        this.context.subscriptions.push(participant);
    }

    async handleRequest(
        request: vscode.ChatRequest,
        _chatContext: vscode.ChatContext,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken,
    ): Promise<void> {
        const prompt = request.prompt.trim();

        // Always render the NTT DATA banner at the top of every response
        stream.markdown(`${NTTDATA_BANNER}\n`);

        if (!prompt || prompt === "help") {
            stream.markdown(this.helpMessage());
            return;
        }

        const parsed = this.parsePrompt(prompt);
        if (!parsed) {
            stream.markdown(`> **${CORPORATE}** — No entendí el comando.\n\n${this.helpMessage()}`);
            return;
        }

        const { version, command, twxPath } = parsed;

        if (!twxPath) {
            stream.markdown(
                `> **${CORPORATE} v${version}** — Por favor indica la ruta al archivo \`.twx\`.\n\n` +
                `Ejemplo: \`@nttdata ${version} ${command} ruta/al/archivo.twx\``,
            );
            return;
        }

        const resolvedPath = this.resolvePath(twxPath);
        if (!resolvedPath) {
            stream.markdown(`> **${CORPORATE}** — Archivo no encontrado: \`${twxPath}\``);
            return;
        }

        stream.progress(`${CORPORATE} v${version} — Ejecutando \`${command}\` en \`${path.basename(resolvedPath)}\`...`);

        try {
            const output = await this.runCommand(command, resolvedPath, version);
            this.formatOutput(command, output, version, resolvedPath, stream);
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : String(err);
            stream.markdown(`> **Error** ejecutando \`${command}\`:\n\`\`\`\n${msg}\n\`\`\``);
        }
    }

    async runCommand(command: string, twxPath: string, version: string): Promise<string> {
        const config    = vscode.workspace.getConfiguration("nttdata.ibm");
        const python    = config.get<string>("pythonPath") || "python";
        const toolsPath = config.get<string>("toolsPath") || this.detectToolsPath();

        const args = ["-m", "ibm_twx_tools", command, twxPath];

        try {
            const { stdout } = await execFileAsync(python, args, {
                cwd: toolsPath,
                timeout: 60_000,
                maxBuffer: 10 * 1024 * 1024,
            });
            return stdout;
        } catch (err: unknown) {
            if (err instanceof Error && "stdout" in err) {
                return (err as NodeJS.ErrnoException & { stdout: string }).stdout || err.message;
            }
            throw err;
        }
    }

    // ------------------------------------------------------------------ private

    private parsePrompt(prompt: string): { version: string; command: TWXCommand; twxPath: string } | null {
        // Patterns:
        //   v1.0 analyze  path/to/file.twx
        //   1.0 analyze   path/to/file.twx
        //   /analyze      path/to/file.twx   (slash command)
        //   analyze       path/to/file.twx
        const re = /^(?:v?([\d.]+)\s+)?(?:\/)?([\w]+)\s*(.*)$/i;
        const match = prompt.match(re);
        if (!match) return null;

        const version = match[1] || SUITE_VERSION;
        const cmdRaw  = match[2].toLowerCase() as TWXCommand;
        const rest    = (match[3] || "").trim();

        if (!VALID_COMMANDS.includes(cmdRaw)) return null;

        return { version, command: cmdRaw, twxPath: rest };
    }

    private resolvePath(raw: string): string | null {
        if (!raw) return null;

        // Absolute path
        if (path.isAbsolute(raw) && fs.existsSync(raw)) return raw;

        // Relative to each workspace folder
        for (const folder of vscode.workspace.workspaceFolders ?? []) {
            const candidate = path.join(folder.uri.fsPath, raw);
            if (fs.existsSync(candidate)) return candidate;
        }

        // Maybe a bare filename — search workspace
        const found = vscode.workspace.findFiles(`**/${raw}`, "**/node_modules/**", 1);
        // We return null here; the caller will handle async search separately if needed
        return null;
    }

    private detectToolsPath(): string {
        // Try to find ibm_twx_tools adjacent to extension or in workspace
        const ext = this.context.extensionUri.fsPath;
        const candidates = [
            path.join(ext, ".."),
            path.join(ext, "..", ".."),
            ...(vscode.workspace.workspaceFolders?.map(f => f.uri.fsPath) ?? []),
        ];
        for (const candidate of candidates) {
            if (fs.existsSync(path.join(candidate, "ibm_twx_tools"))) {
                return candidate;
            }
        }
        return process.cwd();
    }

    private formatOutput(
        command: TWXCommand,
        output: string,
        version: string,
        twxPath: string,
        stream: vscode.ChatResponseStream,
    ): void {
        const header = `## ${CORPORATE} v${version} — \`${command}\` · \`${path.basename(twxPath)}\`\n\n`;

        switch (command) {
            case "analyze":
            case "entities":
            case "services":
            case "endpoints":
            case "entries": {
                try {
                    const data = JSON.parse(output);
                    stream.markdown(header);
                    stream.markdown("```json\n" + JSON.stringify(data, null, 2) + "\n```");
                } catch {
                    stream.markdown(header + output);
                }
                break;
            }

            case "flows":
            case "deps": {
                stream.markdown(header + output);
                break;
            }

            case "docs": {
                stream.markdown(output);
                const saveBtn = new vscode.NotebookRendererMessaging(undefined as never);
                stream.button({
                    command: "nttdata.ibm.generateDocs",
                    title: "Guardar como .md",
                });
                break;
            }

            case "scripts": {
                stream.markdown(header + output);
                break;
            }

            default:
                stream.markdown(header + output);
        }
    }

    private helpMessage(): string {
        const cmds = VALID_COMMANDS.map(
            cmd => `| \`${cmd}\` | ${COMMAND_DESCRIPTIONS[cmd]} |`,
        ).join("\n");

        return [
            `> **IBM TWX Reverse Engineering Suite** — v${SUITE_VERSION} | Corporate: **NTT DATA**`,
            "",
            "---",
            "",
            "### Sintaxis",
            "```",
            "@nttdata <versión> <comando> <ruta/al/archivo.twx>",
            "",
            "Ejemplos:",
            "  @nttdata v1.0 analyze   mi_app.twx",
            "  @nttdata v1.0 services  mi_app.twx",
            "  @nttdata v1.0 flows     mi_app.twx",
            "  @nttdata v1.0 entities  mi_app.twx",
            "  @nttdata v1.0 docs      mi_app.twx",
            "  @nttdata v1.0 scripts   mi_app.twx",
            "  @nttdata v1.0 endpoints mi_app.twx",
            "  @nttdata v1.0 deps      mi_app.twx",
            "  @nttdata v1.0 entries   mi_app.twx",
            "```",
            "",
            "### Comandos disponibles",
            "",
            "| Comando | Descripción |",
            "|:--------|:------------|",
            cmds,
            "",
            "---",
            "_NTT DATA · IBM Integration Designer TWX Reverse Engineering_",
        ].join("\n");
    }
}
