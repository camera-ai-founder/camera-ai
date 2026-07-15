import * as vscode from 'vscode';
import { spawn } from 'child_process';
import * as path from 'path';
import * as fs from 'fs'; 

export function activate(context: vscode.ExtensionContext) {
    console.log('Camera AI & DNA Mutator are active! Protecting the Founder...');

    // ==========================================
    // 1. PRESERVING OUR PAST WORK (Days 1-18)
    // ==========================================
    const cameraAIDisposable = vscode.commands.registerCommand('camera-ai.analyze', async () => {
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

        const pythonProcess = spawn(venvPython, [cliPath, 'generate', highlightedText], { cwd: workspaceRoot });
        let stdoutData = '';
        let stderrData = '';

        pythonProcess.stdout.on('data', (data) => { stdoutData += data.toString(); });
        pythonProcess.stderr.on('data', (data) => { stderrData += data.toString(); });

        pythonProcess.on('close', (code) => {
            if (code !== 0) {
                vscode.window.showErrorMessage(`Camera AI Error: ${stderrData}`);
                return;
            }
            try {
                const cleanOutput = stdoutData.trim();
                const jsonStart = cleanOutput.indexOf('{');
                const jsonEnd = cleanOutput.lastIndexOf('}');
                if (jsonStart === -1 || jsonEnd === -1) return;
                
                const jsonString = cleanOutput.substring(jsonStart, jsonEnd + 1);
                const ontologicalGraph = JSON.parse(jsonString);
                const nodesCount = ontologicalGraph.nodes ? ontologicalGraph.nodes.length : 0;
                const edgesCount = ontologicalGraph.edges ? ontologicalGraph.edges.length : 0;
                
                vscode.window.showInformationMessage(`Camera AI Success! Extracted ${nodesCount} nodes and ${edgesCount} edges.`);
                const outputChannel = vscode.window.createOutputChannel('Camera AI Graph');
                outputChannel.clear();
                outputChannel.appendLine(JSON.stringify(ontologicalGraph, null, 2));
                outputChannel.show(true);
            } catch (error: any) {
                vscode.window.showErrorMessage(`Camera AI Parse Error: ${error.message}`);
            }
        });
    });
    context.subscriptions.push(cameraAIDisposable);

    // ==========================================
    // 2. DAY 19 MISSION: THE DNA MUTATOR & BRAIN
    // ==========================================
    const mutatorDisposable = vscode.commands.registerCommand('dnaMutator.start', () => {
        const panel = vscode.window.createWebviewPanel(
            'dnaMutator', 'DNA Mutator', vscode.ViewColumn.One, { enableScripts: true } 
        );

        const htmlPath = path.join(context.extensionPath, 'media', 'mutator.html');
        panel.webview.html = fs.readFileSync(htmlPath, 'utf-8');

        panel.webview.onDidReceiveMessage(
            message => {
                const workspaceRoot = vscode.workspace.workspaceFolders ? vscode.workspace.workspaceFolders[0].uri.fsPath : '';
                const venvPython = path.join(workspaceRoot, '.venv', 'bin', 'python');

                switch (message.command) {
                    case 'mutateToken':
                        vscode.window.showInformationMessage(`Recompiling reality with token: ${message.token}...`);
                        const synthPath = path.join(workspaceRoot, 'packages', 'core', 'ui_synthesizer.py');
                        const synthProcess = spawn(venvPython, [synthPath, 'mutate', message.token], { cwd: workspaceRoot });
                        
                        synthProcess.on('close', (code) => {
                            if (code === 0) {
                                vscode.window.showInformationMessage(`Reality recompiled! ${message.token} applied.`);
                                panel.webview.postMessage({ command: 'reloadCanvas' });
                            } else {
                                vscode.window.showErrorMessage('Reality recompilation failed.');
                            }
                        });
                        return;

                    case 'suggestEntity':
                        vscode.window.showInformationMessage('Consulting the Brain (brain.py)...');
                        const brainPath = path.join(workspaceRoot, 'packages', 'core', 'brain.py');
                        const brainProcess = spawn(venvPython, [brainPath, 'suggest'], { cwd: workspaceRoot });
                        
                        let brainOutput = '';
                        brainProcess.stdout.on('data', (data) => { brainOutput += data.toString(); });
                        
                        brainProcess.on('close', (code) => {
                            if (code === 0) {
                                try {
                                    const jsonStart = brainOutput.indexOf('{');
                                    const jsonEnd = brainOutput.lastIndexOf('}');
                                    if (jsonStart !== -1 && jsonEnd !== -1) {
                                        const jsonString = brainOutput.substring(jsonStart, jsonEnd + 1);
                                        const node = JSON.parse(jsonString);
                                        const suggestion = `Suggestion: Add '${node.name || 'Unknown Entity'}' to '${node.parent_biome || 'World'}'`;
                                        panel.webview.postMessage({ command: 'displaySuggestion', suggestion: suggestion });
                                    } else {
                                        panel.webview.postMessage({ command: 'displaySuggestion', suggestion: 'Brain returned non-JSON output.' });
                                    }
                                } catch (e) {
                                    panel.webview.postMessage({ command: 'displaySuggestion', suggestion: 'Brain JSON parse error.' });
                                }
                            } else {
                                panel.webview.postMessage({ command: 'displaySuggestion', suggestion: 'Brain failed to respond.' });
                            }
                        });
                        return;
                }
            },
            undefined,
            context.subscriptions
        );
    });
    context.subscriptions.push(mutatorDisposable);
}

export function deactivate(): void {}