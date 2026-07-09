import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
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

export function deactivate() {}

// --- Tree Data Provider for the Sidebar ---
class CameraAITreeDataProvider implements vscode.TreeDataProvider<CameraAIItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<CameraAIItem | undefined | void> = new vscode.EventEmitter<CameraAIItem | undefined | void>();
    readonly onDidChangeTreeData: vscode.Event<CameraAIItem | undefined | void> = this._onDidChangeTreeData.event;

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: CameraAIItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: CameraAIItem): Thenable<CameraAIItem[]> {
        if (element) {
            return Promise.resolve([]);
        } else {
            return Promise.resolve([
                new CameraAIItem('Ontological Graph', vscode.TreeItemCollapsibleState.None),
                new CameraAIItem('Status: ONLINE', vscode.TreeItemCollapsibleState.None),
                new CameraAIItem('Memory Usage: 12%', vscode.TreeItemCollapsibleState.None)
            ]);
        }
    }
}

class CameraAIItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState
    ) {
        super(label, collapsibleState);
        this.tooltip = `Camera AI: ${label}`;
    }
    iconPath = new vscode.ThemeIcon('radio-tower');
}