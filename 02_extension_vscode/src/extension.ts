import * as vscode from "vscode";
import { NTTDATAParticipant } from "./participant";

export function activate(context: vscode.ExtensionContext): void {
    const participant = new NTTDATAParticipant(context);
    participant.register();

    context.subscriptions.push(
        vscode.commands.registerCommand("nttdata.ibm.analyzeFile", async (uri: vscode.Uri) => {
            if (!uri) {
                const files = await vscode.window.showOpenDialog({
                    filters: { "IBM TWX Files": ["twx"] },
                    canSelectMany: false,
                });
                if (!files?.length) return;
                uri = files[0];
            }
            await participant.runCommand("analyze", uri.fsPath, "1.0.0");
        }),

        vscode.commands.registerCommand("nttdata.ibm.generateDocs", async (uri: vscode.Uri) => {
            if (!uri) {
                const files = await vscode.window.showOpenDialog({
                    filters: { "IBM TWX Files": ["twx"] },
                    canSelectMany: false,
                });
                if (!files?.length) return;
                uri = files[0];
            }
            await participant.runCommand("docs", uri.fsPath, "1.0.0");
        }),
    );
}

export function deactivate(): void {}
