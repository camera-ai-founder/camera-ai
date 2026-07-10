import * as vscode from 'vscode';
import { spawn } from 'child_process';
import * as path from 'path';

export function activate(context: vscode.ExtensionContext) {
    console.log('Camera AI is active! Waiting for commands...');

    const disposable = vscode.commands.registerCommand('camera-ai.analyze', async () => {
        
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('Camera AI: Please open a file first.');
            return;
        }

        const selection = editor.selection;
        const highlightedText = editor.document.getText(selection);

        if (!highlightedText || highlightedText.trim() === '') {
            vscode.window.showErrorMessage('Camera AI: Please highlight code first.');
            return;
        }

        const workspaceRoot = vscode.workspace.workspaceFolders 
            ? vscode.workspace.workspaceFolders[0].uri.fsPath 
            : '';

        const venvPython = path.join(workspaceRoot, '.venv', 'bin', 'python');
        const cliPath = path.join(workspaceRoot, 'apps', 'cli', 'camera_cli.py');

        vscode.window.showInformationMessage('Camera AI is thinking...');

        const pythonProcess = spawn(venvPython, [cliPath, 'generate', highlightedText], {
            cwd: workspaceRoot
        });

        let stdoutData = '';
        let stderrData = '';

        pythonProcess.stdout.on('data', (data) => {
            stdoutData += data.toString();
        });

        pythonProcess.stderr.on('data', (data) => {
            stderrData += data.toString();
        });

        pythonProcess.on('close', (code) => {
            if (code !== 0) {
                vscode.window.showErrorMessage(`Camera AI Error: ${stderrData}`);
                return;
            }

            try {
                const cleanOutput = stdoutData.trim();
                const jsonStart = cleanOutput.indexOf('{');
                const jsonEnd = cleanOutput.lastIndexOf('}');
                
                if (jsonStart === -1 || jsonEnd === -1) {
                    vscode.window.showWarningMessage('Camera AI: Output was not JSON.');
                    return;
                }
                
                const jsonString = cleanOutput.substring(jsonStart, jsonEnd + 1);
                const ontologicalGraph = JSON.parse(jsonString);
                
                const nodesCount = ontologicalGraph.nodes ? ontologicalGraph.nodes.length : 0;
                const edgesCount = ontologicalGraph.edges ? ontologicalGraph.edges.length : 0;
                
                vscode.window.showInformationMessage(
                    `Camera AI Success! Extracted ${nodesCount} nodes and ${edgesCount} edges.`
                );
                
                const outputChannel = vscode.window.createOutputChannel('Camera AI Graph');
                outputChannel.clear();
                outputChannel.appendLine(JSON.stringify(ontologicalGraph, null, 2));
                outputChannel.show(true);

            } catch (error: any) {
                vscode.window.showErrorMessage(`Camera AI Parse Error: ${error.message}`);
            }
        });
    });

    context.subscriptions.push(disposable);
}

export function deactivate() {}