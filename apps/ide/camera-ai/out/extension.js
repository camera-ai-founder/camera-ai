"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = require("vscode");
function activate(context) {
    console.log('Camera AI is now active');
    // 1. Register the Hello Command
    let disposableHello = vscode.commands.registerCommand('camera-ai.hello', () => {
        vscode.window.showInformationMessage('Camera AI is online and ready to mutate the Ontological Graph.');
    });
    // 2. Register the Sidebar Tree View
    const treeDataProvider = new CameraAITreeDataProvider();
    const treeView = vscode.window.createTreeView('camera-ai-status', { treeDataProvider });
    // 3. Register the Refresh Command
    let disposableRefresh = vscode.commands.registerCommand('camera-ai.refresh', () => {
        treeDataProvider.refresh();
        vscode.window.showInformationMessage('Camera AI Status Refreshed!');
    });
    context.subscriptions.push(disposableHello, disposableRefresh, treeView);
}
function deactivate() { }
// --- Tree Data Provider for the Sidebar ---
class CameraAITreeDataProvider {
    constructor() {
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        if (element) {
            return Promise.resolve([]);
        }
        else {
            return Promise.resolve([
                new CameraAIItem('Ontological Graph', vscode.TreeItemCollapsibleState.None),
                new CameraAIItem('Status: ONLINE', vscode.TreeItemCollapsibleState.None),
                new CameraAIItem('Memory Usage: 12%', vscode.TreeItemCollapsibleState.None)
            ]);
        }
    }
}
class CameraAIItem extends vscode.TreeItem {
    constructor(label, collapsibleState) {
        super(label, collapsibleState);
        this.label = label;
        this.collapsibleState = collapsibleState;
        this.iconPath = new vscode.ThemeIcon('radio-tower');
        this.tooltip = `Camera AI: ${label}`;
    }
}
//# sourceMappingURL=extension.js.map