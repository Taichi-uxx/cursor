"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const cp = __importStar(require("child_process"));
const util = __importStar(require("util"));
const path = __importStar(require("path"));
const ui_1 = __importDefault(require("./ui"));
const exec = util.promisify(cp.exec);
// Storage for diff content (used by DiffContentProvider)
const diffContentStore = new Map();
// Custom TextDocumentContentProvider for read-only diff views
class DiffContentProvider {
    provideTextDocumentContent(uri) {
        const content = diffContentStore.get(uri.path);
        return content || '';
    }
}
function activate(context) {
    console.log('Claude Code Chat extension is being activated!');
    const provider = new ClaudeChatProvider(context.extensionUri, context);
    const disposable = vscode.commands.registerCommand('claude-code-chat.openChat', (column) => {
        console.log('Claude Code Chat command executed!');
        provider.show(column);
    });
    const loadConversationDisposable = vscode.commands.registerCommand('claude-code-chat.loadConversation', (filename) => {
        provider.loadConversation(filename);
    });
    // Register webview view provider for sidebar chat (using shared provider instance)
    const webviewProvider = new ClaudeChatWebviewProvider(context.extensionUri, context, provider);
    vscode.window.registerWebviewViewProvider('claude-code-chat.chat', webviewProvider);
    // Register custom content provider for read-only diff views
    const diffProvider = new DiffContentProvider();
    context.subscriptions.push(vscode.workspace.registerTextDocumentContentProvider('claude-diff', diffProvider));
    // Listen for configuration changes
    const configChangeDisposable = vscode.workspace.onDidChangeConfiguration(event => {
        if (event.affectsConfiguration('claudeCodeChat.wsl')) {
            console.log('WSL configuration changed, starting new session');
            provider.newSessionOnConfigChange();
        }
    });
    // Create status bar item
    const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.text = "Claude";
    statusBarItem.tooltip = "Open Claude Code Chat (Ctrl+Shift+C)";
    statusBarItem.command = 'claude-code-chat.openChat';
    statusBarItem.show();
    context.subscriptions.push(disposable, loadConversationDisposable, configChangeDisposable, statusBarItem);
    console.log('Claude Code Chat extension activation completed successfully!');
}
function deactivate() { }
class ClaudeChatWebviewProvider {
    _extensionUri;
    _context;
    _chatProvider;
    constructor(_extensionUri, _context, _chatProvider) {
        this._extensionUri = _extensionUri;
        this._context = _context;
        this._chatProvider = _chatProvider;
    }
    resolveWebviewView(webviewView, _context, _token) {
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };
        // Use the shared chat provider instance for the sidebar
        this._chatProvider.showInWebview(webviewView.webview, webviewView);
        // Handle visibility changes to reinitialize when sidebar reopens
        webviewView.onDidChangeVisibility(() => {
            if (webviewView.visible) {
                // Close main panel when sidebar becomes visible
                if (this._chatProvider._panel) {
                    console.log('Closing main panel because sidebar became visible');
                    this._chatProvider._panel.dispose();
                    this._chatProvider._panel = undefined;
                }
                this._chatProvider.reinitializeWebview();
            }
        });
    }
}
class ClaudeChatProvider {
    _extensionUri;
    _context;
    _panel;
    _webview;
    _webviewView;
    _disposables = [];
    _messageHandlerDisposable;
    _totalCost = 0;
    _totalTokensInput = 0;
    _totalTokensOutput = 0;
    _requestCount = 0;
    _subscriptionType; // 'pro', 'max', or undefined for API users
    _accountInfoFetchedThisSession = false; // Track if we fetched account info this session
    _currentSessionId;
    _backupRepoPath;
    _commits = [];
    _conversationsPath;
    // Pending permission requests from stdio control_request messages
    _pendingPermissionRequests = new Map();
    _currentConversation = [];
    _conversationStartTime;
    _conversationIndex = [];
    _currentClaudeProcess;
    _abortController;
    _isWslProcess = false;
    _wslDistro = 'Ubuntu';
    _selectedModel = 'default'; // Default model
    _isProcessing;
    _draftMessage = '';
    constructor(_extensionUri, _context) {
        this._extensionUri = _extensionUri;
        this._context = _context;
        // Initialize backup repository and conversations
        this._initializeBackupRepo();
        this._initializeConversations();
        this._initializeMCPConfig();
        // Load conversation index from workspace state
        this._conversationIndex = this._context.workspaceState.get('claude.conversationIndex', []);
        // Load saved model preference
        this._selectedModel = this._context.workspaceState.get('claude.selectedModel', 'default');
        // Load cached subscription type (will be refreshed on first message)
        this._subscriptionType = this._context.globalState.get('claude.subscriptionType');
        // Resume session from latest conversation
        const latestConversation = this._getLatestConversation();
        this._currentSessionId = latestConversation?.sessionId;
    }
    show(column = vscode.ViewColumn.Two) {
        // Handle case where a URI is passed instead of ViewColumn
        const actualColumn = column instanceof vscode.Uri ? vscode.ViewColumn.Two : column;
        // Close sidebar if it's open
        this._closeSidebar();
        if (this._panel) {
            this._panel.reveal(actualColumn);
            return;
        }
        this._panel = vscode.window.createWebviewPanel('claudeChat', 'Claude Code Chat', actualColumn, {
            enableScripts: true,
            retainContextWhenHidden: true,
            localResourceRoots: [this._extensionUri]
        });
        // Set icon for the webview tab using URI path
        const iconPath = vscode.Uri.joinPath(this._extensionUri, 'icon.png');
        this._panel.iconPath = iconPath;
        this._panel.webview.html = this._getHtmlForWebview();
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
        this._setupWebviewMessageHandler(this._panel.webview);
        this._initializePermissions();
        // Resume session from latest conversation
        const latestConversation = this._getLatestConversation();
        this._currentSessionId = latestConversation?.sessionId;
        // Load latest conversation history if available
        if (latestConversation) {
            this._loadConversationHistory(latestConversation.filename);
        }
        // Send ready message immediately
        setTimeout(() => {
            // If no conversation to load, send ready immediately
            if (!latestConversation) {
                this._sendReadyMessage();
            }
        }, 100);
    }
    _postMessage(message) {
        if (this._panel && this._panel.webview) {
            this._panel.webview.postMessage(message);
        }
        else if (this._webview) {
            this._webview.postMessage(message);
        }
    }
    _sendReadyMessage() {
        // Send current session info if available
        /*if (this._currentSessionId) {
            this._postMessage({
                type: 'sessionResumed',
                data: {
                    sessionId: this._currentSessionId
                }
            });
        }*/
        this._postMessage({
            type: 'ready',
            data: this._isProcessing ? 'Claude is working...' : 'Ready to chat with Claude Code! Type your message below.'
        });
        // Send current model to webview
        this._postMessage({
            type: 'modelSelected',
            model: this._selectedModel
        });
        // Send cached subscription type to webview (will be refreshed on first message)
        if (this._subscriptionType) {
            this._postMessage({
                type: 'accountInfo',
                data: {
                    subscriptionType: this._subscriptionType
                }
            });
        }
        // Send platform information to webview
        this._sendPlatformInfo();
        // Send current settings to webview
        this._sendCurrentSettings();
        // Send saved draft message if any
        if (this._draftMessage) {
            this._postMessage({
                type: 'restoreInputText',
                data: this._draftMessage
            });
        }
    }
    _handleWebviewMessage(message) {
        switch (message.type) {
            case 'sendMessage':
                this._sendMessageToClaude(message.text, message.planMode, message.thinkingMode);
                return;
            case 'newSession':
                this._newSession();
                return;
            case 'restoreCommit':
                this._restoreToCommit(message.commitSha);
                return;
            case 'getConversationList':
                this._sendConversationList();
                return;
            case 'getWorkspaceFiles':
                this._sendWorkspaceFiles(message.searchTerm);
                return;
            case 'selectImageFile':
                this._selectImageFile();
                return;
            case 'loadConversation':
                this.loadConversation(message.filename);
                return;
            case 'stopRequest':
                this._stopClaudeProcess();
                return;
            case 'getSettings':
                this._sendCurrentSettings();
                return;
            case 'updateSettings':
                this._updateSettings(message.settings);
                return;
            case 'getClipboardText':
                this._getClipboardText();
                return;
            case 'selectModel':
                this._setSelectedModel(message.model);
                return;
            case 'openModelTerminal':
                this._openModelTerminal();
                return;
            case 'viewUsage':
                this._openUsageTerminal(message.usageType);
                return;
            case 'executeSlashCommand':
                this._executeSlashCommand(message.command);
                return;
            case 'dismissWSLAlert':
                this._dismissWSLAlert();
                return;
            case 'runInstallCommand':
                this._runInstallCommand();
                return;
            case 'openFile':
                this._openFileInEditor(message.filePath);
                return;
            case 'openDiff':
                this._openDiffEditor(message.oldContent, message.newContent, message.filePath);
                return;
            case 'openDiffByIndex':
                this._openDiffByMessageIndex(message.messageIndex);
                return;
            case 'createImageFile':
                this._createImageFile(message.imageData, message.imageType);
                return;
            case 'permissionResponse':
                this._handlePermissionResponse(message.id, message.approved, message.alwaysAllow);
                return;
            case 'getPermissions':
                this._sendPermissions();
                return;
            case 'removePermission':
                this._removePermission(message.toolName, message.command);
                return;
            case 'addPermission':
                this._addPermission(message.toolName, message.command);
                return;
            case 'loadMCPServers':
                this._loadMCPServers();
                return;
            case 'saveMCPServer':
                this._saveMCPServer(message.name, message.config);
                return;
            case 'deleteMCPServer':
                this._deleteMCPServer(message.name);
                return;
            case 'getCustomSnippets':
                this._sendCustomSnippets();
                return;
            case 'saveCustomSnippet':
                this._saveCustomSnippet(message.snippet);
                return;
            case 'deleteCustomSnippet':
                this._deleteCustomSnippet(message.snippetId);
                return;
            case 'enableYoloMode':
                this._enableYoloMode();
                return;
            case 'saveInputText':
                this._saveInputText(message.text);
                return;
        }
    }
    _setupWebviewMessageHandler(webview) {
        // Dispose of any existing message handler
        if (this._messageHandlerDisposable) {
            this._messageHandlerDisposable.dispose();
        }
        // Set up new message handler
        this._messageHandlerDisposable = webview.onDidReceiveMessage(message => this._handleWebviewMessage(message), null, this._disposables);
    }
    _closeSidebar() {
        if (this._webviewView) {
            // Switch VS Code to show Explorer view instead of chat sidebar
            vscode.commands.executeCommand('workbench.view.explorer');
        }
    }
    showInWebview(webview, webviewView) {
        // Close main panel if it's open
        if (this._panel) {
            console.log('Closing main panel because sidebar is opening');
            this._panel.dispose();
            this._panel = undefined;
        }
        this._webview = webview;
        this._webviewView = webviewView;
        this._webview.html = this._getHtmlForWebview();
        this._setupWebviewMessageHandler(this._webview);
        this._initializePermissions();
        // Initialize the webview
        this._initializeWebview();
    }
    _initializeWebview() {
        // Resume session from latest conversation
        const latestConversation = this._getLatestConversation();
        this._currentSessionId = latestConversation?.sessionId;
        // Load latest conversation history if available
        if (latestConversation) {
            this._loadConversationHistory(latestConversation.filename);
        }
        else {
            // If no conversation to load, send ready immediately
            setTimeout(() => {
                this._sendReadyMessage();
            }, 100);
        }
    }
    reinitializeWebview() {
        // Only reinitialize if we have a webview (sidebar)
        if (this._webview) {
            this._initializePermissions();
            this._initializeWebview();
            // Set up message handler for the webview
            this._setupWebviewMessageHandler(this._webview);
        }
    }
    async _sendMessageToClaude(message, planMode, thinkingMode) {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        const cwd = workspaceFolder ? workspaceFolder.uri.fsPath : process.cwd();
        // Get thinking intensity setting
        const configThink = vscode.workspace.getConfiguration('claudeCodeChat');
        const thinkingIntensity = configThink.get('thinking.intensity', 'think');
        // Prepend thinking mode instructions if enabled
        let actualMessage = message;
        if (thinkingMode) {
            let thinkingPrompt = '';
            const thinkingMesssage = ' THROUGH THIS STEP BY STEP: \n';
            switch (thinkingIntensity) {
                case 'think':
                    thinkingPrompt = 'THINK';
                    break;
                case 'think-hard':
                    thinkingPrompt = 'THINK HARD';
                    break;
                case 'think-harder':
                    thinkingPrompt = 'THINK HARDER';
                    break;
                case 'ultrathink':
                    thinkingPrompt = 'ULTRATHINK';
                    break;
                default:
                    thinkingPrompt = 'THINK';
            }
            actualMessage = thinkingPrompt + thinkingMesssage + actualMessage;
        }
        this._isProcessing = true;
        // Clear draft message since we're sending it
        this._draftMessage = '';
        // Show original user input in chat and save to conversation (without mode prefixes)
        this._sendAndSaveMessage({
            type: 'userInput',
            data: message
        });
        // Set processing state to true
        this._postMessage({
            type: 'setProcessing',
            data: { isProcessing: true }
        });
        // Create backup commit before Claude makes changes
        try {
            await this._createBackupCommit(message);
        }
        catch (e) {
            console.log("error", e);
        }
        // Show loading indicator
        this._postMessage({
            type: 'loading',
            data: 'Claude is working...'
        });
        // Build command arguments with session management
        // Use stream-json for both input and output to enable bidirectional communication
        // This is required for stdio-based permission prompts
        const args = [
            '--output-format', 'stream-json',
            '--input-format', 'stream-json',
            '--verbose'
        ];
        // Get configuration
        const config = vscode.workspace.getConfiguration('claudeCodeChat');
        const yoloMode = config.get('permissions.yoloMode', false);
        if (yoloMode) {
            // Yolo mode: skip all permissions
            args.push('--dangerously-skip-permissions');
        }
        else {
            // Use stdio-based permission prompts (no MCP server needed)
            args.push('--permission-prompt-tool', 'stdio');
        }
        // Add MCP config if user has custom servers configured
        const mcpConfigPath = this.getMCPConfigPath();
        if (mcpConfigPath) {
            args.push('--mcp-config', this.convertToWSLPath(mcpConfigPath));
        }
        // Add plan mode if enabled
        if (planMode) {
            args.push('--permission-mode', 'plan');
        }
        // Add model selection if not using default
        if (this._selectedModel && this._selectedModel !== 'default') {
            args.push('--model', this._selectedModel);
        }
        // Add session resume if we have a current session
        if (this._currentSessionId) {
            args.push('--resume', this._currentSessionId);
            console.log('Resuming session:', this._currentSessionId);
        }
        else {
            console.log('Starting new session');
        }
        console.log('Claude command args:', args);
        const wslEnabled = config.get('wsl.enabled', false);
        const wslDistro = config.get('wsl.distro', 'Ubuntu');
        const nodePath = config.get('wsl.nodePath', '/usr/bin/node');
        const claudePath = config.get('wsl.claudePath', '/usr/local/bin/claude');
        let claudeProcess;
        // Create new AbortController for this request
        this._abortController = new AbortController();
        if (wslEnabled) {
            // Use WSL with bash -ic for proper environment loading
            console.log('Using WSL configuration:', { wslDistro, nodePath, claudePath });
            const wslCommand = `"${nodePath}" --no-warnings --enable-source-maps "${claudePath}" ${args.join(' ')}`;
            // Track WSL state for proper process termination
            this._isWslProcess = true;
            this._wslDistro = wslDistro;
            claudeProcess = cp.spawn('wsl', ['-d', wslDistro, 'bash', '-ic', wslCommand], {
                signal: this._abortController.signal,
                detached: process.platform !== 'win32',
                cwd: cwd,
                stdio: ['pipe', 'pipe', 'pipe'],
                env: {
                    ...process.env,
                    FORCE_COLOR: '0',
                    NO_COLOR: '1'
                }
            });
        }
        else {
            // Not using WSL
            this._isWslProcess = false;
            // Use native claude command
            console.log('Using native Claude command');
            claudeProcess = cp.spawn('claude', args, {
                signal: this._abortController.signal,
                shell: process.platform === 'win32',
                detached: process.platform !== 'win32',
                cwd: cwd,
                stdio: ['pipe', 'pipe', 'pipe'],
                env: {
                    ...process.env,
                    FORCE_COLOR: '0',
                    NO_COLOR: '1'
                }
            });
        }
        // Store process reference for potential termination
        this._currentClaudeProcess = claudeProcess;
        // Send the message to Claude's stdin as JSON (stream-json input format)
        // Don't end stdin yet - we need to keep it open for permission responses
        if (claudeProcess.stdin) {
            // First, send an initialize request to get account info (once per session)
            if (!this._accountInfoFetchedThisSession) {
                this._accountInfoFetchedThisSession = true;
                const initRequest = {
                    type: 'control_request',
                    request_id: 'init-' + Date.now(),
                    request: {
                        subtype: 'initialize'
                    }
                };
                claudeProcess.stdin.write(JSON.stringify(initRequest) + '\n');
            }
            const userMessage = {
                type: 'user',
                session_id: this._currentSessionId || '',
                message: {
                    role: 'user',
                    content: [{ type: 'text', text: actualMessage }]
                },
                parent_tool_use_id: null
            };
            claudeProcess.stdin.write(JSON.stringify(userMessage) + '\n');
        }
        let rawOutput = '';
        let errorOutput = '';
        if (claudeProcess.stdout) {
            claudeProcess.stdout.on('data', (data) => {
                rawOutput += data.toString();
                // Process JSON stream line by line
                const lines = rawOutput.split('\n');
                rawOutput = lines.pop() || ''; // Keep incomplete line for next chunk
                for (const line of lines) {
                    if (line.trim()) {
                        try {
                            const jsonData = JSON.parse(line.trim());
                            // Handle control_request messages (permission requests via stdio)
                            if (jsonData.type === 'control_request') {
                                this._handleControlRequest(jsonData, claudeProcess).catch(err => {
                                    console.error('Error handling control request:', err);
                                });
                                continue;
                            }
                            // Handle control_response messages (responses to our initialize request)
                            if (jsonData.type === 'control_response') {
                                this._handleControlResponse(jsonData);
                                continue;
                            }
                            // Handle result message - end stdin when done
                            if (jsonData.type === 'result') {
                                if (claudeProcess.stdin && !claudeProcess.stdin.destroyed) {
                                    claudeProcess.stdin.end();
                                }
                            }
                            this._processJsonStreamData(jsonData);
                        }
                        catch (error) {
                            console.log('Failed to parse JSON line:', line, error);
                        }
                    }
                }
            });
        }
        if (claudeProcess.stderr) {
            claudeProcess.stderr.on('data', (data) => {
                errorOutput += data.toString();
            });
        }
        claudeProcess.on('close', (code) => {
            console.log('Claude process closed with code:', code);
            console.log('Claude stderr output:', errorOutput);
            if (!this._currentClaudeProcess) {
                return;
            }
            // Clear process reference
            this._currentClaudeProcess = undefined;
            // Cancel any pending permission requests (process is gone)
            this._cancelPendingPermissionRequests();
            // Clear loading indicator and set processing to false
            this._postMessage({
                type: 'clearLoading'
            });
            // Reset processing state
            this._isProcessing = false;
            // Clear processing state
            this._postMessage({
                type: 'setProcessing',
                data: { isProcessing: false }
            });
            if (code !== 0 && errorOutput.trim()) {
                // Error with output
                this._sendAndSaveMessage({
                    type: 'error',
                    data: errorOutput.trim()
                });
            }
        });
        claudeProcess.on('error', (error) => {
            console.log('Claude process error:', error.message);
            if (!this._currentClaudeProcess) {
                return;
            }
            // Clear process reference
            this._currentClaudeProcess = undefined;
            // Cancel any pending permission requests (process is gone)
            this._cancelPendingPermissionRequests();
            this._postMessage({
                type: 'clearLoading'
            });
            this._isProcessing = false;
            // Clear processing state
            this._postMessage({
                type: 'setProcessing',
                data: { isProcessing: false }
            });
            // Check if claude command is not installed
            if (error.message.includes('ENOENT') || error.message.includes('command not found')) {
                this._postMessage({
                    type: 'showInstallModal'
                });
            }
            else {
                this._sendAndSaveMessage({
                    type: 'error',
                    data: `Error running Claude: ${error.message}`
                });
            }
        });
    }
    async _processJsonStreamData(jsonData) {
        switch (jsonData.type) {
            case 'system':
                if (jsonData.subtype === 'init') {
                    // System initialization message - session ID will be captured from final result
                    console.log('System initialized');
                    this._currentSessionId = jsonData.session_id;
                    //this._sendAndSaveMessage({ type: 'init', data: { sessionId: jsonData.session_id; } })
                    // Show session info in UI
                    this._sendAndSaveMessage({
                        type: 'sessionInfo',
                        data: {
                            sessionId: jsonData.session_id,
                            tools: jsonData.tools || [],
                            mcpServers: jsonData.mcp_servers || []
                        }
                    });
                }
                else if (jsonData.subtype === 'status') {
                    // Handle status changes (e.g., compacting)
                    if (jsonData.status === 'compacting') {
                        console.log('Conversation compacting started');
                        this._sendAndSaveMessage({
                            type: 'compacting',
                            data: { isCompacting: true }
                        });
                    }
                    else if (jsonData.status === null) {
                        console.log('Status cleared');
                        this._sendAndSaveMessage({
                            type: 'compacting',
                            data: { isCompacting: false }
                        });
                    }
                }
                else if (jsonData.subtype === 'compact_boundary') {
                    // Compact boundary - conversation was compacted, reset token counts
                    console.log('Compact boundary received', jsonData.compact_metadata);
                    // Reset tokens since the conversation is now summarized
                    this._totalTokensInput = 0;
                    this._totalTokensOutput = 0;
                    this._sendAndSaveMessage({
                        type: 'compactBoundary',
                        data: {
                            trigger: jsonData.compact_metadata?.trigger,
                            preTokens: jsonData.compact_metadata?.pre_tokens
                        }
                    });
                }
                break;
            case 'assistant':
                if (jsonData.message && jsonData.message.content) {
                    // Track token usage in real-time if available
                    if (jsonData.message.usage) {
                        this._totalTokensInput += jsonData.message.usage.input_tokens || 0;
                        this._totalTokensOutput += jsonData.message.usage.output_tokens || 0;
                        // Send real-time token update to webview
                        this._sendAndSaveMessage({
                            type: 'updateTokens',
                            data: {
                                totalTokensInput: this._totalTokensInput,
                                totalTokensOutput: this._totalTokensOutput,
                                currentInputTokens: jsonData.message.usage.input_tokens || 0,
                                currentOutputTokens: jsonData.message.usage.output_tokens || 0,
                                cacheCreationTokens: jsonData.message.usage.cache_creation_input_tokens || 0,
                                cacheReadTokens: jsonData.message.usage.cache_read_input_tokens || 0
                            }
                        });
                    }
                    // Process each content item in the assistant message
                    for (const content of jsonData.message.content) {
                        if (content.type === 'text' && content.text.trim()) {
                            // Show text content and save to conversation
                            this._sendAndSaveMessage({
                                type: 'output',
                                data: content.text.trim()
                            });
                        }
                        else if (content.type === 'thinking' && content.thinking.trim()) {
                            // Show thinking content and save to conversation
                            this._sendAndSaveMessage({
                                type: 'thinking',
                                data: content.thinking.trim()
                            });
                        }
                        else if (content.type === 'tool_use') {
                            // Show tool execution with better formatting
                            const toolInfo = `🔧 Executing: ${content.name}`;
                            let toolInput = '';
                            let fileContentBefore;
                            if (content.input) {
                                // Special formatting for TodoWrite to make it more readable
                                if (content.name === 'TodoWrite' && content.input.todos) {
                                    toolInput = '\nTodo List Update:';
                                    for (const todo of content.input.todos) {
                                        const status = todo.status === 'completed' ? '✅' :
                                            todo.status === 'in_progress' ? '🔄' : '⏳';
                                        toolInput += `\n${status} ${todo.content} (priority: ${todo.priority})`;
                                    }
                                }
                                else {
                                    // Send raw input to UI for formatting
                                    toolInput = '';
                                }
                                // For Edit/MultiEdit/Write, read current file content (before state)
                                if ((content.name === 'Edit' || content.name === 'MultiEdit' || content.name === 'Write') && content.input.file_path) {
                                    try {
                                        const fileUri = vscode.Uri.file(content.input.file_path);
                                        const fileData = await vscode.workspace.fs.readFile(fileUri);
                                        fileContentBefore = Buffer.from(fileData).toString('utf8');
                                    }
                                    catch {
                                        // File might not exist yet (for Write), that's ok
                                        fileContentBefore = '';
                                    }
                                }
                            }
                            // Compute startLine(s) while we have the file content
                            let startLine;
                            let startLines;
                            if (fileContentBefore !== undefined) {
                                if (content.name === 'Edit' && content.input.old_string) {
                                    const position = fileContentBefore.indexOf(content.input.old_string);
                                    if (position !== -1) {
                                        const textBefore = fileContentBefore.substring(0, position);
                                        startLine = (textBefore.match(/\n/g) || []).length + 1;
                                    }
                                    else {
                                        startLine = 1;
                                    }
                                }
                                else if (content.name === 'MultiEdit' && content.input.edits) {
                                    startLines = content.input.edits.map((edit) => {
                                        if (edit.old_string) {
                                            const position = fileContentBefore.indexOf(edit.old_string);
                                            if (position !== -1) {
                                                const textBefore = fileContentBefore.substring(0, position);
                                                return (textBefore.match(/\n/g) || []).length + 1;
                                            }
                                        }
                                        return 1;
                                    });
                                }
                            }
                            // Show tool use and save to conversation
                            this._sendAndSaveMessage({
                                type: 'toolUse',
                                data: {
                                    toolInfo: toolInfo,
                                    toolInput: toolInput,
                                    rawInput: content.input,
                                    toolName: content.name,
                                    fileContentBefore: fileContentBefore,
                                    startLine: startLine,
                                    startLines: startLines
                                }
                            });
                        }
                    }
                }
                break;
            case 'user':
                if (jsonData.message && jsonData.message.content) {
                    // Process tool results from user messages
                    for (const content of jsonData.message.content) {
                        if (content.type === 'tool_result') {
                            let resultContent = content.content || 'Tool executed successfully';
                            // Stringify if content is an object or array
                            if (typeof resultContent === 'object' && resultContent !== null) {
                                resultContent = JSON.stringify(resultContent, null, 2);
                            }
                            const isError = content.is_error || false;
                            // Find the last tool use to get the tool name, input, and computed startLine
                            const lastToolUse = this._currentConversation[this._currentConversation.length - 1];
                            const toolName = lastToolUse?.data?.toolName;
                            const rawInput = lastToolUse?.data?.rawInput;
                            const startLine = lastToolUse?.data?.startLine;
                            const startLines = lastToolUse?.data?.startLines;
                            // For Edit/MultiEdit/Write, read current file content (after state)
                            let fileContentAfter;
                            if ((toolName === 'Edit' || toolName === 'MultiEdit' || toolName === 'Write') && rawInput?.file_path && !isError) {
                                try {
                                    const fileUri = vscode.Uri.file(rawInput.file_path);
                                    const fileData = await vscode.workspace.fs.readFile(fileUri);
                                    fileContentAfter = Buffer.from(fileData).toString('utf8');
                                }
                                catch {
                                    // File read failed, that's ok
                                }
                            }
                            // Don't send tool result for Read and TodoWrite tools unless there's an error
                            if ((toolName === 'Read' || toolName === 'TodoWrite') && !isError) {
                                // Still send to UI to hide loading state, but mark it as hidden
                                this._sendAndSaveMessage({
                                    type: 'toolResult',
                                    data: {
                                        content: resultContent,
                                        isError: isError,
                                        toolUseId: content.tool_use_id,
                                        toolName: toolName,
                                        rawInput: rawInput,
                                        hidden: true
                                    }
                                });
                            }
                            else {
                                // Show tool result and save to conversation
                                this._sendAndSaveMessage({
                                    type: 'toolResult',
                                    data: {
                                        content: resultContent,
                                        isError: isError,
                                        toolUseId: content.tool_use_id,
                                        toolName: toolName,
                                        rawInput: rawInput,
                                        fileContentAfter: fileContentAfter,
                                        startLine: startLine,
                                        startLines: startLines
                                    }
                                });
                            }
                        }
                    }
                }
                break;
            case 'result':
                if (jsonData.subtype === 'success') {
                    // Check for login errors
                    if (jsonData.is_error && jsonData.result && jsonData.result.includes('Invalid API key')) {
                        this._handleLoginRequired();
                        return;
                    }
                    this._isProcessing = false;
                    // Capture session ID from final result
                    if (jsonData.session_id) {
                        const isNewSession = !this._currentSessionId;
                        const sessionChanged = this._currentSessionId && this._currentSessionId !== jsonData.session_id;
                        console.log('Session ID found in result:', {
                            sessionId: jsonData.session_id,
                            isNewSession,
                            sessionChanged,
                            currentSessionId: this._currentSessionId
                        });
                        this._currentSessionId = jsonData.session_id;
                        // Show session info in UI
                        this._sendAndSaveMessage({
                            type: 'sessionInfo',
                            data: {
                                sessionId: jsonData.session_id,
                                tools: jsonData.tools || [],
                                mcpServers: jsonData.mcp_servers || []
                            }
                        });
                    }
                    // Clear processing state
                    this._postMessage({
                        type: 'setProcessing',
                        data: { isProcessing: false }
                    });
                    // Update cumulative tracking
                    this._requestCount++;
                    if (jsonData.total_cost_usd) {
                        this._totalCost += jsonData.total_cost_usd;
                    }
                    console.log('Result received:', {
                        cost: jsonData.total_cost_usd,
                        duration: jsonData.duration_ms,
                        turns: jsonData.num_turns
                    });
                    // Send updated totals to webview
                    this._postMessage({
                        type: 'updateTotals',
                        data: {
                            totalCost: this._totalCost,
                            totalTokensInput: this._totalTokensInput,
                            totalTokensOutput: this._totalTokensOutput,
                            requestCount: this._requestCount,
                            currentCost: jsonData.total_cost_usd,
                            currentDuration: jsonData.duration_ms,
                            currentTurns: jsonData.num_turns
                        }
                    });
                }
                break;
        }
    }
    async _newSession() {
        this._isProcessing = false;
        // Update UI state
        this._postMessage({
            type: 'setProcessing',
            data: { isProcessing: false }
        });
        // Kill Claude process and all child processes
        await this._killClaudeProcess();
        // Clear current session
        this._currentSessionId = undefined;
        // Clear commits and conversation
        this._commits = [];
        this._currentConversation = [];
        this._conversationStartTime = undefined;
        // Reset counters
        this._totalCost = 0;
        this._totalTokensInput = 0;
        this._totalTokensOutput = 0;
        this._requestCount = 0;
        // Notify webview to clear all messages and reset session
        this._postMessage({
            type: 'sessionCleared'
        });
    }
    newSessionOnConfigChange() {
        // Reinitialize MCP config with new WSL paths
        this._initializeMCPConfig();
        // Start a new session due to configuration change
        this._newSession();
        // Show notification to user
        vscode.window.showInformationMessage('WSL configuration changed. Started a new Claude session.', 'OK');
        // Send message to webview about the config change
        this._sendAndSaveMessage({
            type: 'configChanged',
            data: '⚙️ WSL configuration changed. Started a new session.'
        });
    }
    _handleLoginRequired() {
        this._isProcessing = false;
        // Clear processing state
        this._postMessage({
            type: 'setProcessing',
            data: { isProcessing: false }
        });
        // Show login required message
        this._postMessage({
            type: 'loginRequired'
        });
        // Get configuration to check if WSL is enabled
        const config = vscode.workspace.getConfiguration('claudeCodeChat');
        const wslEnabled = config.get('wsl.enabled', false);
        const wslDistro = config.get('wsl.distro', 'Ubuntu');
        const nodePath = config.get('wsl.nodePath', '/usr/bin/node');
        const claudePath = config.get('wsl.claudePath', '/usr/local/bin/claude');
        // Open terminal and run claude login
        const terminal = vscode.window.createTerminal({
            name: 'Claude Login',
            location: { viewColumn: vscode.ViewColumn.One }
        });
        if (wslEnabled) {
            terminal.sendText(`wsl -d ${wslDistro} ${nodePath} --no-warnings --enable-source-maps ${claudePath}`);
        }
        else {
            terminal.sendText('claude');
        }
        terminal.show();
        // Show info message
        vscode.window.showInformationMessage('Please login with your Claude plan or API key in the terminal, then come back to this chat.', 'OK');
        // Send message to UI about terminal
        this._postMessage({
            type: 'terminalOpened',
            data: `Please login with your Claude plan or API key in the terminal, then come back to this chat.`,
        });
    }
    async _initializeBackupRepo() {
        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
                return;
            }
            const storagePath = this._context.storageUri?.fsPath;
            if (!storagePath) {
                console.error('No workspace storage available');
                return;
            }
            console.log('Workspace storage path:', storagePath);
            this._backupRepoPath = path.join(storagePath, 'backups', '.git');
            // Create backup git directory if it doesn't exist
            try {
                await vscode.workspace.fs.stat(vscode.Uri.file(this._backupRepoPath));
            }
            catch {
                await vscode.workspace.fs.createDirectory(vscode.Uri.file(this._backupRepoPath));
                const workspacePath = workspaceFolder.uri.fsPath;
                // Initialize git repo with workspace as work-tree
                await exec(`git --git-dir="${this._backupRepoPath}" --work-tree="${workspacePath}" init`);
                await exec(`git --git-dir="${this._backupRepoPath}" config user.name "Claude Code Chat"`);
                await exec(`git --git-dir="${this._backupRepoPath}" config user.email "claude@anthropic.com"`);
                console.log(`Initialized backup repository at: ${this._backupRepoPath}`);
            }
        }
        catch (error) {
            console.error('Failed to initialize backup repository:', error.message);
        }
    }
    async _createBackupCommit(userMessage) {
        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder || !this._backupRepoPath) {
                return;
            }
            const workspacePath = workspaceFolder.uri.fsPath;
            const now = new Date();
            const timestamp = now.toISOString().replace(/[:.]/g, '-');
            const displayTimestamp = now.toISOString();
            const commitMessage = `Before: ${userMessage.substring(0, 50)}${userMessage.length > 50 ? '...' : ''}`;
            // Add all files using git-dir and work-tree (excludes .git automatically)
            await exec(`git --git-dir="${this._backupRepoPath}" --work-tree="${workspacePath}" add -A`);
            // Check if this is the first commit (no HEAD exists yet)
            let isFirstCommit = false;
            try {
                await exec(`git --git-dir="${this._backupRepoPath}" rev-parse HEAD`);
            }
            catch {
                isFirstCommit = true;
            }
            // Check if there are changes to commit
            const { stdout: status } = await exec(`git --git-dir="${this._backupRepoPath}" --work-tree="${workspacePath}" status --porcelain`);
            // Always create a checkpoint, even if no files changed
            let actualMessage;
            if (isFirstCommit) {
                actualMessage = `Initial backup: ${userMessage.substring(0, 50)}${userMessage.length > 50 ? '...' : ''}`;
            }
            else if (status.trim()) {
                actualMessage = commitMessage;
            }
            else {
                actualMessage = `Checkpoint (no changes): ${userMessage.substring(0, 50)}${userMessage.length > 50 ? '...' : ''}`;
            }
            // Create commit with --allow-empty to ensure checkpoint is always created
            await exec(`git --git-dir="${this._backupRepoPath}" --work-tree="${workspacePath}" commit --allow-empty -m "${actualMessage}"`);
            const { stdout: sha } = await exec(`git --git-dir="${this._backupRepoPath}" rev-parse HEAD`);
            // Store commit info
            const commitInfo = {
                id: `commit-${timestamp}`,
                sha: sha.trim(),
                message: actualMessage,
                timestamp: displayTimestamp
            };
            this._commits.push(commitInfo);
            // Show restore option in UI and save to conversation
            this._sendAndSaveMessage({
                type: 'showRestoreOption',
                data: commitInfo
            });
            console.log(`Created backup commit: ${commitInfo.sha.substring(0, 8)} - ${actualMessage}`);
        }
        catch (error) {
            console.error('Failed to create backup commit:', error.message);
        }
    }
    async _restoreToCommit(commitSha) {
        try {
            const commit = this._commits.find(c => c.sha === commitSha);
            if (!commit) {
                this._postMessage({
                    type: 'restoreError',
                    data: 'Commit not found'
                });
                return;
            }
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder || !this._backupRepoPath) {
                vscode.window.showErrorMessage('No workspace folder or backup repository available.');
                return;
            }
            const workspacePath = workspaceFolder.uri.fsPath;
            this._postMessage({
                type: 'restoreProgress',
                data: 'Restoring files from backup...'
            });
            // Restore files directly to workspace using git checkout
            await exec(`git --git-dir="${this._backupRepoPath}" --work-tree="${workspacePath}" checkout ${commitSha} -- .`);
            vscode.window.showInformationMessage(`Restored to commit: ${commit.message}`);
            this._sendAndSaveMessage({
                type: 'restoreSuccess',
                data: {
                    message: `Successfully restored to: ${commit.message}`,
                    commitSha: commitSha
                }
            });
        }
        catch (error) {
            console.error('Failed to restore commit:', error.message);
            vscode.window.showErrorMessage(`Failed to restore commit: ${error.message}`);
            this._postMessage({
                type: 'restoreError',
                data: `Failed to restore: ${error.message}`
            });
        }
    }
    async _initializeConversations() {
        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
                return;
            }
            const storagePath = this._context.storageUri?.fsPath;
            if (!storagePath) {
                return;
            }
            this._conversationsPath = path.join(storagePath, 'conversations');
            // Create conversations directory if it doesn't exist
            try {
                await vscode.workspace.fs.stat(vscode.Uri.file(this._conversationsPath));
            }
            catch {
                await vscode.workspace.fs.createDirectory(vscode.Uri.file(this._conversationsPath));
                console.log(`Created conversations directory at: ${this._conversationsPath}`);
            }
        }
        catch (error) {
            console.error('Failed to initialize conversations directory:', error.message);
        }
    }
    async _initializeMCPConfig() {
        try {
            const storagePath = this._context.storageUri?.fsPath;
            if (!storagePath) {
                return;
            }
            // Create MCP config directory
            const mcpConfigDir = path.join(storagePath, 'mcp');
            try {
                await vscode.workspace.fs.stat(vscode.Uri.file(mcpConfigDir));
            }
            catch {
                await vscode.workspace.fs.createDirectory(vscode.Uri.file(mcpConfigDir));
                console.log(`Created MCP config directory at: ${mcpConfigDir}`);
            }
            // Create or update mcp-servers.json, preserving user's custom servers
            // Note: Permissions are now handled via stdio, not MCP
            const mcpConfigPath = path.join(mcpConfigDir, 'mcp-servers.json');
            // Load existing config or create new one
            let mcpConfig = { mcpServers: {} };
            const mcpConfigUri = vscode.Uri.file(mcpConfigPath);
            try {
                const existingContent = await vscode.workspace.fs.readFile(mcpConfigUri);
                mcpConfig = JSON.parse(new TextDecoder().decode(existingContent));
                console.log('Loaded existing MCP config, preserving user servers');
            }
            catch {
                console.log('No existing MCP config found, creating new one');
            }
            // Ensure mcpServers exists
            if (!mcpConfig.mcpServers) {
                mcpConfig.mcpServers = {};
            }
            // Remove old permissions server if it exists (migrating from file-based to stdio)
            if (mcpConfig.mcpServers['claude-code-chat-permissions']) {
                delete mcpConfig.mcpServers['claude-code-chat-permissions'];
                console.log('Removed legacy permissions MCP server (now using stdio)');
            }
            const configContent = new TextEncoder().encode(JSON.stringify(mcpConfig, null, 2));
            await vscode.workspace.fs.writeFile(mcpConfigUri, configContent);
            console.log(`Updated MCP config at: ${mcpConfigPath}`);
        }
        catch (error) {
            console.error('Failed to initialize MCP config:', error.message);
        }
    }
    /**
     * Check if a tool is pre-approved in local permissions
     */
    async _isToolPreApproved(toolName, input) {
        try {
            const storagePath = this._context.storageUri?.fsPath;
            if (!storagePath)
                return false;
            const permissionsUri = vscode.Uri.file(path.join(storagePath, 'permissions', 'permissions.json'));
            let permissions = { alwaysAllow: {} };
            try {
                const content = await vscode.workspace.fs.readFile(permissionsUri);
                permissions = JSON.parse(new TextDecoder().decode(content));
            }
            catch {
                return false; // No permissions file
            }
            const toolPermission = permissions.alwaysAllow?.[toolName];
            if (toolPermission === true) {
                // Tool is fully approved (all commands/inputs)
                return true;
            }
            if (Array.isArray(toolPermission) && toolName === 'Bash' && input.command) {
                // Check if the command matches any approved pattern
                const command = input.command.trim();
                for (const pattern of toolPermission) {
                    if (this._matchesPattern(command, pattern)) {
                        return true;
                    }
                }
            }
            return false;
        }
        catch (error) {
            console.error('Error checking pre-approved permissions:', error);
            return false;
        }
    }
    /**
     * Check if a command matches a permission pattern (supports * wildcard)
     */
    _matchesPattern(command, pattern) {
        if (pattern === command)
            return true;
        // Handle wildcard patterns like "npm install *"
        if (pattern.endsWith(' *')) {
            const prefix = pattern.slice(0, -1); // Remove the *
            return command.startsWith(prefix);
        }
        // Handle exact match patterns
        return false;
    }
    /**
     * Handle control_response messages from Claude CLI via stdio
     * This is used to get account info from the initialize request
     */
    _handleControlResponse(controlResponse) {
        // Structure: controlResponse.response.response.account
        // The outer response has subtype/request_id, inner response has the actual data
        const innerResponse = controlResponse.response?.response;
        // Check if this is an initialize response with account info
        if (innerResponse?.account) {
            const account = innerResponse.account;
            this._subscriptionType = account.subscriptionType;
            console.log('Account info received:', {
                subscriptionType: account.subscriptionType,
                email: account.email
            });
            // Save to globalState for persistence
            this._context.globalState.update('claude.subscriptionType', this._subscriptionType);
            // Send subscription type to UI
            this._postMessage({
                type: 'accountInfo',
                data: {
                    subscriptionType: this._subscriptionType
                }
            });
        }
    }
    /**
     * Handle control_request messages from Claude CLI via stdio
     * This is the new permission flow that replaces the MCP file-based approach
     */
    async _handleControlRequest(controlRequest, claudeProcess) {
        const request = controlRequest.request;
        const requestId = controlRequest.request_id;
        // Only handle can_use_tool requests (permission requests)
        if (request?.subtype !== 'can_use_tool') {
            console.log('Ignoring non-permission control request:', request?.subtype);
            return;
        }
        const toolName = request.tool_name || 'Unknown Tool';
        const input = request.input || {};
        const suggestions = request.permission_suggestions;
        const toolUseId = request.tool_use_id;
        console.log(`Permission request for tool: ${toolName}, requestId: ${requestId}`);
        // Check if this tool is pre-approved
        const isPreApproved = await this._isToolPreApproved(toolName, input);
        if (isPreApproved) {
            console.log(`Tool ${toolName} is pre-approved, auto-allowing`);
            // Auto-approve without showing UI
            this._sendPermissionResponse(requestId, true, {
                requestId,
                toolName,
                input,
                suggestions,
                toolUseId
            }, false);
            return;
        }
        // Store the request data so we can respond later
        this._pendingPermissionRequests.set(requestId, {
            requestId,
            toolName,
            input,
            suggestions,
            toolUseId
        });
        // Generate pattern for Bash commands (for display purposes)
        let pattern;
        if (toolName === 'Bash' && input.command) {
            pattern = this.getCommandPattern(input.command);
        }
        // Send permission request to the UI with pending status
        this._sendAndSaveMessage({
            type: 'permissionRequest',
            data: {
                id: requestId,
                tool: toolName,
                input: input,
                pattern: pattern,
                suggestions: suggestions,
                decisionReason: request.decision_reason,
                blockedPath: request.blocked_path,
                status: 'pending'
            }
        });
    }
    /**
     * Send permission response back to Claude CLI via stdin
     */
    _sendPermissionResponse(requestId, approved, pendingRequest, alwaysAllow) {
        if (!this._currentClaudeProcess?.stdin || this._currentClaudeProcess.stdin.destroyed) {
            console.error('Cannot send permission response: stdin not available');
            return;
        }
        let response;
        if (approved) {
            response = {
                type: 'control_response',
                response: {
                    subtype: 'success',
                    request_id: requestId,
                    response: {
                        behavior: 'allow',
                        updatedInput: pendingRequest.input,
                        // Pass back suggestions if user chose "always allow"
                        updatedPermissions: alwaysAllow ? pendingRequest.suggestions : undefined,
                        toolUseID: pendingRequest.toolUseId
                    }
                }
            };
        }
        else {
            response = {
                type: 'control_response',
                response: {
                    subtype: 'success',
                    request_id: requestId,
                    response: {
                        behavior: 'deny',
                        message: 'User denied permission',
                        interrupt: true,
                        toolUseID: pendingRequest.toolUseId
                    }
                }
            };
        }
        const responseJson = JSON.stringify(response) + '\n';
        console.log('Sending permission response:', responseJson);
        console.log('Always allow:', alwaysAllow, 'Suggestions included:', !!pendingRequest.suggestions);
        this._currentClaudeProcess.stdin.write(responseJson);
    }
    async _initializePermissions() {
        // No longer needed - permissions are handled via stdio
        // This method is kept for compatibility but does nothing
    }
    /**
     * Handle permission response from webview UI
     * Sends control_response back to Claude CLI via stdin
     */
    _handlePermissionResponse(id, approved, alwaysAllow) {
        const pendingRequest = this._pendingPermissionRequests.get(id);
        if (!pendingRequest) {
            console.error('No pending permission request found for id:', id);
            return;
        }
        // Remove from pending requests
        this._pendingPermissionRequests.delete(id);
        // Send the response to Claude via stdin
        this._sendPermissionResponse(id, approved, pendingRequest, alwaysAllow);
        // Update the permission request status in UI
        this._postMessage({
            type: 'updatePermissionStatus',
            data: {
                id: id,
                status: approved ? 'approved' : 'denied'
            }
        });
        // Also save to local permissions.json for UI display purposes
        if (alwaysAllow && approved) {
            void this._saveLocalPermission(pendingRequest.toolName, pendingRequest.input);
        }
    }
    /**
     * Cancel all pending permission requests (called when process ends)
     */
    _cancelPendingPermissionRequests() {
        for (const [id, _request] of this._pendingPermissionRequests) {
            this._postMessage({
                type: 'updatePermissionStatus',
                data: {
                    id: id,
                    status: 'cancelled'
                }
            });
        }
        this._pendingPermissionRequests.clear();
    }
    /**
     * Save permission to local storage for UI display in settings
     * Note: The actual "always allow" is handled by Claude via updatedPermissions
     */
    async _saveLocalPermission(toolName, input) {
        try {
            const storagePath = this._context.storageUri?.fsPath;
            if (!storagePath)
                return;
            // Ensure permissions directory exists
            const permissionsDir = path.join(storagePath, 'permissions');
            try {
                await vscode.workspace.fs.stat(vscode.Uri.file(permissionsDir));
            }
            catch {
                await vscode.workspace.fs.createDirectory(vscode.Uri.file(permissionsDir));
            }
            // Load existing permissions
            const permissionsUri = vscode.Uri.file(path.join(permissionsDir, 'permissions.json'));
            let permissions = { alwaysAllow: {} };
            try {
                const content = await vscode.workspace.fs.readFile(permissionsUri);
                permissions = JSON.parse(new TextDecoder().decode(content));
            }
            catch {
                // File doesn't exist yet
            }
            // Add the permission
            if (toolName === 'Bash' && input.command) {
                if (!permissions.alwaysAllow[toolName]) {
                    permissions.alwaysAllow[toolName] = [];
                }
                if (Array.isArray(permissions.alwaysAllow[toolName])) {
                    const pattern = this.getCommandPattern(input.command);
                    if (!permissions.alwaysAllow[toolName].includes(pattern)) {
                        permissions.alwaysAllow[toolName].push(pattern);
                    }
                }
            }
            else {
                permissions.alwaysAllow[toolName] = true;
            }
            // Save permissions
            const permissionsContent = new TextEncoder().encode(JSON.stringify(permissions, null, 2));
            await vscode.workspace.fs.writeFile(permissionsUri, permissionsContent);
            console.log(`Saved local permission for ${toolName}`);
        }
        catch (error) {
            console.error('Error saving local permission:', error);
        }
    }
    getCommandPattern(command) {
        const parts = command.trim().split(/\s+/);
        if (parts.length === 0)
            return command;
        const baseCmd = parts[0];
        const subCmd = parts.length > 1 ? parts[1] : '';
        // Common patterns that should use wildcards
        const patterns = [
            // Package managers
            ['npm', 'install', 'npm install *'],
            ['npm', 'i', 'npm i *'],
            ['npm', 'add', 'npm add *'],
            ['npm', 'remove', 'npm remove *'],
            ['npm', 'uninstall', 'npm uninstall *'],
            ['npm', 'update', 'npm update *'],
            ['npm', 'run', 'npm run *'],
            ['yarn', 'add', 'yarn add *'],
            ['yarn', 'remove', 'yarn remove *'],
            ['yarn', 'install', 'yarn install *'],
            ['pnpm', 'install', 'pnpm install *'],
            ['pnpm', 'add', 'pnpm add *'],
            ['pnpm', 'remove', 'pnpm remove *'],
            // Git commands
            ['git', 'add', 'git add *'],
            ['git', 'commit', 'git commit *'],
            ['git', 'push', 'git push *'],
            ['git', 'pull', 'git pull *'],
            ['git', 'checkout', 'git checkout *'],
            ['git', 'branch', 'git branch *'],
            ['git', 'merge', 'git merge *'],
            ['git', 'clone', 'git clone *'],
            ['git', 'reset', 'git reset *'],
            ['git', 'rebase', 'git rebase *'],
            ['git', 'tag', 'git tag *'],
            // Docker commands
            ['docker', 'run', 'docker run *'],
            ['docker', 'build', 'docker build *'],
            ['docker', 'exec', 'docker exec *'],
            ['docker', 'logs', 'docker logs *'],
            ['docker', 'stop', 'docker stop *'],
            ['docker', 'start', 'docker start *'],
            ['docker', 'rm', 'docker rm *'],
            ['docker', 'rmi', 'docker rmi *'],
            ['docker', 'pull', 'docker pull *'],
            ['docker', 'push', 'docker push *'],
            // Build tools
            ['make', '', 'make *'],
            ['cargo', 'build', 'cargo build *'],
            ['cargo', 'run', 'cargo run *'],
            ['cargo', 'test', 'cargo test *'],
            ['cargo', 'install', 'cargo install *'],
            ['mvn', 'compile', 'mvn compile *'],
            ['mvn', 'test', 'mvn test *'],
            ['mvn', 'package', 'mvn package *'],
            ['gradle', 'build', 'gradle build *'],
            ['gradle', 'test', 'gradle test *'],
            // System commands
            ['curl', '', 'curl *'],
            ['wget', '', 'wget *'],
            ['ssh', '', 'ssh *'],
            ['scp', '', 'scp *'],
            ['rsync', '', 'rsync *'],
            ['tar', '', 'tar *'],
            ['zip', '', 'zip *'],
            ['unzip', '', 'unzip *'],
            // Development tools
            ['node', '', 'node *'],
            ['python', '', 'python *'],
            ['python3', '', 'python3 *'],
            ['pip', 'install', 'pip install *'],
            ['pip3', 'install', 'pip3 install *'],
            ['composer', 'install', 'composer install *'],
            ['composer', 'require', 'composer require *'],
            ['bundle', 'install', 'bundle install *'],
            ['gem', 'install', 'gem install *'],
        ];
        // Find matching pattern
        for (const [cmd, sub, pattern] of patterns) {
            if (baseCmd === cmd && (sub === '' || subCmd === sub)) {
                return pattern;
            }
        }
        // Default: return exact command
        return command;
    }
    async _sendPermissions() {
        try {
            const storagePath = this._context.storageUri?.fsPath;
            if (!storagePath) {
                this._postMessage({
                    type: 'permissionsData',
                    data: { alwaysAllow: {} }
                });
                return;
            }
            const permissionsUri = vscode.Uri.file(path.join(storagePath, 'permissions', 'permissions.json'));
            let permissions = { alwaysAllow: {} };
            try {
                const content = await vscode.workspace.fs.readFile(permissionsUri);
                permissions = JSON.parse(new TextDecoder().decode(content));
            }
            catch {
                // File doesn't exist or can't be read, use default permissions
            }
            this._postMessage({
                type: 'permissionsData',
                data: permissions
            });
        }
        catch (error) {
            console.error('Error sending permissions:', error);
            this._postMessage({
                type: 'permissionsData',
                data: { alwaysAllow: {} }
            });
        }
    }
    async _removePermission(toolName, command) {
        try {
            const storagePath = this._context.storageUri?.fsPath;
            if (!storagePath)
                return;
            const permissionsUri = vscode.Uri.file(path.join(storagePath, 'permissions', 'permissions.json'));
            let permissions = { alwaysAllow: {} };
            try {
                const content = await vscode.workspace.fs.readFile(permissionsUri);
                permissions = JSON.parse(new TextDecoder().decode(content));
            }
            catch {
                // File doesn't exist or can't be read, nothing to remove
                return;
            }
            // Remove the permission
            if (command === null) {
                // Remove entire tool permission
                delete permissions.alwaysAllow[toolName];
            }
            else {
                // Remove specific command from tool permissions
                if (Array.isArray(permissions.alwaysAllow[toolName])) {
                    permissions.alwaysAllow[toolName] = permissions.alwaysAllow[toolName].filter((cmd) => cmd !== command);
                    // If no commands left, remove the tool entirely
                    if (permissions.alwaysAllow[toolName].length === 0) {
                        delete permissions.alwaysAllow[toolName];
                    }
                }
            }
            // Save updated permissions
            const permissionsContent = new TextEncoder().encode(JSON.stringify(permissions, null, 2));
            await vscode.workspace.fs.writeFile(permissionsUri, permissionsContent);
            // Send updated permissions to UI
            this._sendPermissions();
            console.log(`Removed permission for ${toolName}${command ? ` command: ${command}` : ''}`);
        }
        catch (error) {
            console.error('Error removing permission:', error);
        }
    }
    async _addPermission(toolName, command) {
        try {
            const storagePath = this._context.storageUri?.fsPath;
            if (!storagePath)
                return;
            const permissionsUri = vscode.Uri.file(path.join(storagePath, 'permissions', 'permissions.json'));
            let permissions = { alwaysAllow: {} };
            try {
                const content = await vscode.workspace.fs.readFile(permissionsUri);
                permissions = JSON.parse(new TextDecoder().decode(content));
            }
            catch {
                // File doesn't exist, use default permissions
            }
            // Add the new permission
            if (command === null || command === '') {
                // Allow all commands for this tool
                permissions.alwaysAllow[toolName] = true;
            }
            else {
                // Add specific command pattern
                if (!permissions.alwaysAllow[toolName]) {
                    permissions.alwaysAllow[toolName] = [];
                }
                // Convert to array if it's currently set to true
                if (permissions.alwaysAllow[toolName] === true) {
                    permissions.alwaysAllow[toolName] = [];
                }
                if (Array.isArray(permissions.alwaysAllow[toolName])) {
                    // For Bash commands, convert to pattern using existing logic
                    let commandToAdd = command;
                    if (toolName === 'Bash') {
                        commandToAdd = this.getCommandPattern(command);
                    }
                    // Add if not already present
                    if (!permissions.alwaysAllow[toolName].includes(commandToAdd)) {
                        permissions.alwaysAllow[toolName].push(commandToAdd);
                    }
                }
            }
            // Ensure permissions directory exists
            const permissionsDir = vscode.Uri.file(path.dirname(permissionsUri.fsPath));
            try {
                await vscode.workspace.fs.stat(permissionsDir);
            }
            catch {
                await vscode.workspace.fs.createDirectory(permissionsDir);
            }
            // Save updated permissions
            const permissionsContent = new TextEncoder().encode(JSON.stringify(permissions, null, 2));
            await vscode.workspace.fs.writeFile(permissionsUri, permissionsContent);
            // Send updated permissions to UI
            this._sendPermissions();
            console.log(`Added permission for ${toolName}${command ? ` command: ${command}` : ' (all commands)'}`);
        }
        catch (error) {
            console.error('Error adding permission:', error);
        }
    }
    async _loadMCPServers() {
        try {
            const mcpConfigPath = this.getMCPConfigPath();
            if (!mcpConfigPath) {
                this._postMessage({ type: 'mcpServers', data: {} });
                return;
            }
            const mcpConfigUri = vscode.Uri.file(mcpConfigPath);
            let mcpConfig = { mcpServers: {} };
            try {
                const content = await vscode.workspace.fs.readFile(mcpConfigUri);
                mcpConfig = JSON.parse(new TextDecoder().decode(content));
            }
            catch (error) {
                console.log('MCP config file not found or error reading:', error);
                // File doesn't exist, return empty servers
            }
            // Filter out internal servers before sending to UI
            const filteredServers = Object.fromEntries(Object.entries(mcpConfig.mcpServers || {}).filter(([name]) => name !== 'claude-code-chat-permissions'));
            this._postMessage({ type: 'mcpServers', data: filteredServers });
        }
        catch (error) {
            console.error('Error loading MCP servers:', error);
            this._postMessage({ type: 'mcpServerError', data: { error: 'Failed to load MCP servers' } });
        }
    }
    async _saveMCPServer(name, config) {
        try {
            const mcpConfigPath = this.getMCPConfigPath();
            if (!mcpConfigPath) {
                this._postMessage({ type: 'mcpServerError', data: { error: 'Storage path not available' } });
                return;
            }
            const mcpConfigUri = vscode.Uri.file(mcpConfigPath);
            let mcpConfig = { mcpServers: {} };
            // Load existing config
            try {
                const content = await vscode.workspace.fs.readFile(mcpConfigUri);
                mcpConfig = JSON.parse(new TextDecoder().decode(content));
            }
            catch {
                // File doesn't exist, use default structure
            }
            // Ensure mcpServers exists
            if (!mcpConfig.mcpServers) {
                mcpConfig.mcpServers = {};
            }
            // Add/update the server
            mcpConfig.mcpServers[name] = config;
            // Ensure directory exists
            const mcpDir = vscode.Uri.file(path.dirname(mcpConfigPath));
            try {
                await vscode.workspace.fs.stat(mcpDir);
            }
            catch {
                await vscode.workspace.fs.createDirectory(mcpDir);
            }
            // Save the config
            const configContent = new TextEncoder().encode(JSON.stringify(mcpConfig, null, 2));
            await vscode.workspace.fs.writeFile(mcpConfigUri, configContent);
            this._postMessage({ type: 'mcpServerSaved', data: { name } });
            console.log(`Saved MCP server: ${name}`);
        }
        catch (error) {
            console.error('Error saving MCP server:', error);
            this._postMessage({ type: 'mcpServerError', data: { error: 'Failed to save MCP server' } });
        }
    }
    async _deleteMCPServer(name) {
        try {
            const mcpConfigPath = this.getMCPConfigPath();
            if (!mcpConfigPath) {
                this._postMessage({ type: 'mcpServerError', data: { error: 'Storage path not available' } });
                return;
            }
            const mcpConfigUri = vscode.Uri.file(mcpConfigPath);
            let mcpConfig = { mcpServers: {} };
            // Load existing config
            try {
                const content = await vscode.workspace.fs.readFile(mcpConfigUri);
                mcpConfig = JSON.parse(new TextDecoder().decode(content));
            }
            catch {
                // File doesn't exist, nothing to delete
                this._postMessage({ type: 'mcpServerError', data: { error: 'MCP config file not found' } });
                return;
            }
            // Delete the server
            if (mcpConfig.mcpServers && mcpConfig.mcpServers[name]) {
                delete mcpConfig.mcpServers[name];
                // Save the updated config
                const configContent = new TextEncoder().encode(JSON.stringify(mcpConfig, null, 2));
                await vscode.workspace.fs.writeFile(mcpConfigUri, configContent);
                this._postMessage({ type: 'mcpServerDeleted', data: { name } });
                console.log(`Deleted MCP server: ${name}`);
            }
            else {
                this._postMessage({ type: 'mcpServerError', data: { error: `Server '${name}' not found` } });
            }
        }
        catch (error) {
            console.error('Error deleting MCP server:', error);
            this._postMessage({ type: 'mcpServerError', data: { error: 'Failed to delete MCP server' } });
        }
    }
    async _sendCustomSnippets() {
        try {
            const customSnippets = this._context.globalState.get('customPromptSnippets', {});
            this._postMessage({
                type: 'customSnippetsData',
                data: customSnippets
            });
        }
        catch (error) {
            console.error('Error loading custom snippets:', error);
            this._postMessage({
                type: 'customSnippetsData',
                data: {}
            });
        }
    }
    async _saveCustomSnippet(snippet) {
        try {
            const customSnippets = this._context.globalState.get('customPromptSnippets', {});
            customSnippets[snippet.id] = snippet;
            await this._context.globalState.update('customPromptSnippets', customSnippets);
            this._postMessage({
                type: 'customSnippetSaved',
                data: { snippet }
            });
            console.log('Saved custom snippet:', snippet.name);
        }
        catch (error) {
            console.error('Error saving custom snippet:', error);
            this._postMessage({
                type: 'error',
                data: 'Failed to save custom snippet'
            });
        }
    }
    async _deleteCustomSnippet(snippetId) {
        try {
            const customSnippets = this._context.globalState.get('customPromptSnippets', {});
            if (customSnippets[snippetId]) {
                delete customSnippets[snippetId];
                await this._context.globalState.update('customPromptSnippets', customSnippets);
                this._postMessage({
                    type: 'customSnippetDeleted',
                    data: { snippetId }
                });
                console.log('Deleted custom snippet:', snippetId);
            }
            else {
                this._postMessage({
                    type: 'error',
                    data: 'Snippet not found'
                });
            }
        }
        catch (error) {
            console.error('Error deleting custom snippet:', error);
            this._postMessage({
                type: 'error',
                data: 'Failed to delete custom snippet'
            });
        }
    }
    convertToWSLPath(windowsPath) {
        const config = vscode.workspace.getConfiguration('claudeCodeChat');
        const wslEnabled = config.get('wsl.enabled', false);
        if (wslEnabled && windowsPath.match(/^[a-zA-Z]:/)) {
            // Convert C:\Users\... to /mnt/c/Users/...
            return windowsPath.replace(/^([a-zA-Z]):/, '/mnt/$1').toLowerCase().replace(/\\/g, '/');
        }
        return windowsPath;
    }
    getMCPConfigPath() {
        const storagePath = this._context.storageUri?.fsPath;
        if (!storagePath) {
            return undefined;
        }
        const configPath = path.join(storagePath, 'mcp', 'mcp-servers.json');
        return path.join(configPath);
    }
    _sendAndSaveMessage(message) {
        // Initialize conversation if this is the first message
        if (this._currentConversation.length === 0) {
            this._conversationStartTime = new Date().toISOString();
        }
        // The message index will be the current length (0-indexed position after push)
        const messageIndex = this._currentConversation.length;
        // For tool messages that support diff, include the message index
        const messageToSend = (message.type === 'toolUse' || message.type === 'toolResult')
            ? { ...message, data: { ...message.data, messageIndex } }
            : message;
        // Send to UI using the helper method
        this._postMessage(messageToSend);
        // Strip fileContentBefore/fileContentAfter from saved data to reduce storage
        // Keep startLine/startLines which are small and needed for accurate line numbers on reload
        let dataToSave = message.data;
        if (message.type === 'toolUse' || message.type === 'toolResult') {
            const { fileContentBefore, fileContentAfter, ...rest } = message.data || {};
            dataToSave = rest; // startLine and startLines are preserved in rest
        }
        // Save to conversation
        this._currentConversation.push({
            timestamp: new Date().toISOString(),
            messageType: message.type,
            data: dataToSave
        });
        // Persist conversation
        void this._saveCurrentConversation();
    }
    async _saveCurrentConversation() {
        if (!this._conversationsPath || this._currentConversation.length === 0) {
            return;
        }
        if (!this._currentSessionId) {
            return;
        }
        try {
            // Create filename from first user message and timestamp
            const firstUserMessage = this._currentConversation.find(m => m.messageType === 'userInput');
            const firstMessage = firstUserMessage ? firstUserMessage.data : 'conversation';
            const startTime = this._conversationStartTime || new Date().toISOString();
            const sessionId = this._currentSessionId || 'unknown';
            // Clean and truncate first message for filename
            const cleanMessage = firstMessage
                .replace(/[^a-zA-Z0-9\s]/g, '') // Remove special chars
                .replace(/\s+/g, '-') // Replace spaces with dashes
                .substring(0, 50) // Limit length
                .toLowerCase();
            const datePrefix = startTime.substring(0, 16).replace('T', '_').replace(/:/g, '-');
            const filename = `${datePrefix}_${cleanMessage}.json`;
            const conversationData = {
                sessionId: sessionId,
                startTime: this._conversationStartTime,
                endTime: new Date().toISOString(),
                messageCount: this._currentConversation.length,
                totalCost: this._totalCost,
                totalTokens: {
                    input: this._totalTokensInput,
                    output: this._totalTokensOutput
                },
                messages: this._currentConversation,
                filename
            };
            const filePath = path.join(this._conversationsPath, filename);
            const content = new TextEncoder().encode(JSON.stringify(conversationData, null, 2));
            await vscode.workspace.fs.writeFile(vscode.Uri.file(filePath), content);
            // Update conversation index
            this._updateConversationIndex(filename, conversationData);
            console.log(`Saved conversation: ${filename}`, this._conversationsPath);
        }
        catch (error) {
            console.error('Failed to save conversation:', error.message);
        }
    }
    async loadConversation(filename) {
        // Load the conversation history
        await this._loadConversationHistory(filename);
    }
    _sendConversationList() {
        this._postMessage({
            type: 'conversationList',
            data: this._conversationIndex
        });
    }
    async _sendWorkspaceFiles(searchTerm) {
        try {
            // Always get all files and filter on the backend for better search results
            const files = await vscode.workspace.findFiles('**/*', '{**/node_modules/**,**/.git/**,**/dist/**,**/build/**,**/.next/**,**/.nuxt/**,**/target/**,**/bin/**,**/obj/**}', 500 // Reasonable limit for filtering
            );
            let fileList = files.map(file => {
                const relativePath = vscode.workspace.asRelativePath(file);
                return {
                    name: file.path.split('/').pop() || '',
                    path: relativePath,
                    fsPath: file.fsPath
                };
            });
            // Filter results based on search term
            if (searchTerm && searchTerm.trim()) {
                const term = searchTerm.toLowerCase();
                fileList = fileList.filter(file => {
                    const fileName = file.name.toLowerCase();
                    const filePath = file.path.toLowerCase();
                    // Check if term matches filename or any part of the path
                    return fileName.includes(term) ||
                        filePath.includes(term) ||
                        filePath.split('/').some(segment => segment.includes(term));
                });
            }
            // Sort and limit results
            fileList = fileList
                .sort((a, b) => a.name.localeCompare(b.name))
                .slice(0, 50);
            this._postMessage({
                type: 'workspaceFiles',
                data: fileList
            });
        }
        catch (error) {
            console.error('Error getting workspace files:', error);
            this._postMessage({
                type: 'workspaceFiles',
                data: []
            });
        }
    }
    async _selectImageFile() {
        try {
            // Show VS Code's native file picker for images
            const result = await vscode.window.showOpenDialog({
                canSelectFiles: true,
                canSelectFolders: false,
                canSelectMany: true,
                title: 'Select image files',
                filters: {
                    'Images': ['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'bmp']
                }
            });
            if (result && result.length > 0) {
                // Send the selected file paths back to webview
                result.forEach(uri => {
                    this._postMessage({
                        type: 'imagePath',
                        path: uri.fsPath
                    });
                });
            }
        }
        catch (error) {
            console.error('Error selecting image files:', error);
        }
    }
    async _killProcessGroup(pid, signal = 'SIGTERM') {
        if (this._isWslProcess) {
            // WSL: Kill processes inside WSL using pkill
            // The Windows PID won't work inside WSL, so we kill by name
            try {
                // Kill all node/claude processes started by this session inside WSL
                const killSignal = signal === 'SIGKILL' ? '-9' : '-15';
                await exec(`wsl -d ${this._wslDistro} pkill ${killSignal} -f "claude"`);
            }
            catch {
                // Process may already be dead or pkill not available
            }
            // Also kill the Windows-side wsl process
            try {
                await exec(`taskkill /pid ${pid} /t /f`);
            }
            catch {
                // Process may already be dead
            }
        }
        else if (process.platform === 'win32') {
            // Windows: Use taskkill with /T flag for tree kill
            try {
                await exec(`taskkill /pid ${pid} /t /f`);
            }
            catch {
                // Process may already be dead
            }
        }
        else {
            // Unix: Kill process group with negative PID
            try {
                process.kill(-pid, signal);
            }
            catch {
                // Process may already be dead
            }
        }
    }
    async _killClaudeProcess() {
        const processToKill = this._currentClaudeProcess;
        const pid = processToKill?.pid;
        // 1. Abort via controller (clean API)
        this._abortController?.abort();
        this._abortController = undefined;
        // 2. Clear reference immediately
        this._currentClaudeProcess = undefined;
        if (!pid) {
            return;
        }
        console.log(`Terminating Claude process group (PID: ${pid})...`);
        // 3. Kill process group (handles children)
        await this._killProcessGroup(pid, 'SIGTERM');
        // 4. Wait for process to exit, with timeout
        const exitPromise = new Promise((resolve) => {
            if (processToKill?.killed) {
                resolve();
                return;
            }
            processToKill?.once('exit', () => resolve());
        });
        const timeoutPromise = new Promise((resolve) => {
            setTimeout(() => resolve(), 2000);
        });
        await Promise.race([exitPromise, timeoutPromise]);
        // 5. Force kill if still running
        if (processToKill && !processToKill.killed) {
            console.log(`Force killing Claude process group (PID: ${pid})...`);
            await this._killProcessGroup(pid, 'SIGKILL');
        }
        console.log('Claude process group terminated');
    }
    async _stopClaudeProcess() {
        console.log('Stop request received');
        this._isProcessing = false;
        // Update UI state
        this._postMessage({
            type: 'setProcessing',
            data: { isProcessing: false }
        });
        await this._killClaudeProcess();
        this._postMessage({
            type: 'clearLoading'
        });
        // Send stop confirmation message directly to UI and save
        this._sendAndSaveMessage({
            type: 'error',
            data: '⏹️ Claude code was stopped.'
        });
    }
    _updateConversationIndex(filename, conversationData) {
        // Extract first and last user messages
        const userMessages = conversationData.messages.filter((m) => m.messageType === 'userInput');
        const firstUserMessage = userMessages.length > 0 ? userMessages[0].data : 'No user message';
        const lastUserMessage = userMessages.length > 0 ? userMessages[userMessages.length - 1].data : firstUserMessage;
        // Create or update index entry
        const indexEntry = {
            filename: filename,
            sessionId: conversationData.sessionId,
            startTime: conversationData.startTime || '',
            endTime: conversationData.endTime,
            messageCount: conversationData.messageCount,
            totalCost: conversationData.totalCost,
            firstUserMessage: firstUserMessage.substring(0, 100), // Truncate for storage
            lastUserMessage: lastUserMessage.substring(0, 100)
        };
        // Remove any existing entry for this session (in case of updates)
        this._conversationIndex = this._conversationIndex.filter(entry => entry.filename !== conversationData.filename);
        // Add new entry at the beginning (most recent first)
        this._conversationIndex.unshift(indexEntry);
        // Keep only last 50 conversations to avoid workspace state bloat
        if (this._conversationIndex.length > 50) {
            this._conversationIndex = this._conversationIndex.slice(0, 50);
        }
        // Save to workspace state
        this._context.workspaceState.update('claude.conversationIndex', this._conversationIndex);
    }
    _getLatestConversation() {
        return this._conversationIndex.length > 0 ? this._conversationIndex[0] : undefined;
    }
    async _loadConversationHistory(filename) {
        console.log("_loadConversationHistory");
        if (!this._conversationsPath) {
            return;
        }
        try {
            const filePath = path.join(this._conversationsPath, filename);
            console.log("filePath", filePath);
            let conversationData;
            try {
                const fileUri = vscode.Uri.file(filePath);
                const content = await vscode.workspace.fs.readFile(fileUri);
                conversationData = JSON.parse(new TextDecoder().decode(content));
            }
            catch {
                return;
            }
            // Load conversation into current state
            this._currentConversation = conversationData.messages || [];
            this._conversationStartTime = conversationData.startTime;
            this._totalCost = conversationData.totalCost || 0;
            this._totalTokensInput = conversationData.totalTokens?.input || 0;
            this._totalTokensOutput = conversationData.totalTokens?.output || 0;
            // Clear UI messages first, then send all messages to recreate the conversation
            setTimeout(() => {
                // Clear existing messages
                this._postMessage({
                    type: 'sessionCleared'
                });
                let requestStartTime;
                // Small delay to ensure messages are cleared before loading new ones
                setTimeout(() => {
                    const messages = this._currentConversation;
                    for (let i = 0; i < messages.length; i++) {
                        const message = messages[i];
                        if (message.messageType === 'permissionRequest') {
                            const isLast = i === messages.length - 1;
                            if (!isLast) {
                                continue;
                            }
                        }
                        // For tool messages, include the message index so Open Diff buttons work
                        let messageData = (message.messageType === 'toolUse' || message.messageType === 'toolResult')
                            ? { ...message.data, messageIndex: i }
                            : message.data;
                        // For permission requests loaded from history, mark pending ones as expired
                        // ONLY if there's no active Claude process (i.e., VS Code was restarted)
                        if (message.messageType === 'permissionRequest' &&
                            message.data?.status === 'pending' &&
                            !this._currentClaudeProcess) {
                            messageData = { ...message.data, status: 'expired' };
                        }
                        this._postMessage({
                            type: message.messageType,
                            data: messageData
                        });
                        if (message.messageType === 'userInput') {
                            try {
                                requestStartTime = new Date(message.timestamp).getTime();
                            }
                            catch (e) {
                                console.log(e);
                            }
                        }
                    }
                    // Send updated totals
                    this._postMessage({
                        type: 'updateTotals',
                        data: {
                            totalCost: this._totalCost,
                            totalTokensInput: this._totalTokensInput,
                            totalTokensOutput: this._totalTokensOutput,
                            requestCount: this._requestCount
                        }
                    });
                    // Restore processing state if the conversation was saved while processing
                    if (this._isProcessing) {
                        this._postMessage({
                            type: 'setProcessing',
                            data: { isProcessing: this._isProcessing, requestStartTime }
                        });
                    }
                    // Mark any pending permission requests as expired ONLY if there's no active Claude process
                    // (i.e., VS Code was restarted, not just the panel was closed/reopened)
                    if (!this._currentClaudeProcess) {
                        this._postMessage({
                            type: 'expirePendingPermissions'
                        });
                    }
                    // Send ready message after conversation is loaded
                    this._sendReadyMessage();
                }, 50);
            }, 100); // Small delay to ensure webview is ready
            console.log(`Loaded conversation history: ${filename}`);
        }
        catch (error) {
            console.error('Failed to load conversation history:', error.message);
        }
    }
    _getHtmlForWebview() {
        return (0, ui_1.default)(vscode.env?.isTelemetryEnabled);
    }
    _sendCurrentSettings() {
        const config = vscode.workspace.getConfiguration('claudeCodeChat');
        const settings = {
            'thinking.intensity': config.get('thinking.intensity', 'think'),
            'wsl.enabled': config.get('wsl.enabled', false),
            'wsl.distro': config.get('wsl.distro', 'Ubuntu'),
            'wsl.nodePath': config.get('wsl.nodePath', '/usr/bin/node'),
            'wsl.claudePath': config.get('wsl.claudePath', '/usr/local/bin/claude'),
            'permissions.yoloMode': config.get('permissions.yoloMode', false)
        };
        this._postMessage({
            type: 'settingsData',
            data: settings
        });
    }
    async _enableYoloMode() {
        try {
            // Update VS Code configuration to enable YOLO mode
            const config = vscode.workspace.getConfiguration('claudeCodeChat');
            // Clear any global setting and set workspace setting
            await config.update('permissions.yoloMode', true, vscode.ConfigurationTarget.Workspace);
            console.log('YOLO Mode enabled - all future permissions will be skipped');
            // Send updated settings to UI
            this._sendCurrentSettings();
        }
        catch (error) {
            console.error('Error enabling YOLO mode:', error);
        }
    }
    _saveInputText(text) {
        this._draftMessage = text || '';
    }
    async _updateSettings(settings) {
        const config = vscode.workspace.getConfiguration('claudeCodeChat');
        try {
            for (const [key, value] of Object.entries(settings)) {
                if (key === 'permissions.yoloMode') {
                    // YOLO mode is workspace-specific
                    await config.update(key, value, vscode.ConfigurationTarget.Workspace);
                }
                else {
                    // Other settings are global (user-wide)
                    await config.update(key, value, vscode.ConfigurationTarget.Global);
                }
            }
            console.log('Settings updated:', settings);
        }
        catch (error) {
            console.error('Failed to update settings:', error);
            vscode.window.showErrorMessage('Failed to update settings');
        }
    }
    async _getClipboardText() {
        try {
            const text = await vscode.env.clipboard.readText();
            this._postMessage({
                type: 'clipboardText',
                data: text
            });
        }
        catch (error) {
            console.error('Failed to read clipboard:', error);
        }
    }
    _setSelectedModel(model) {
        // Validate model name to prevent issues mentioned in the GitHub issue
        const validModels = ['opus', 'sonnet', 'default'];
        if (validModels.includes(model)) {
            this._selectedModel = model;
            console.log('Model selected:', model);
            // Store the model preference in workspace state
            this._context.workspaceState.update('claude.selectedModel', model);
            // Show confirmation
            vscode.window.showInformationMessage(`Claude model switched to: ${model.charAt(0).toUpperCase() + model.slice(1)}`);
        }
        else {
            console.error('Invalid model selected:', model);
            vscode.window.showErrorMessage(`Invalid model: ${model}. Please select Opus, Sonnet, or Default.`);
        }
    }
    _openModelTerminal() {
        const config = vscode.workspace.getConfiguration('claudeCodeChat');
        const wslEnabled = config.get('wsl.enabled', false);
        const wslDistro = config.get('wsl.distro', 'Ubuntu');
        const nodePath = config.get('wsl.nodePath', '/usr/bin/node');
        const claudePath = config.get('wsl.claudePath', '/usr/local/bin/claude');
        // Build command arguments
        const args = ['/model'];
        // Add session resume if we have a current session
        if (this._currentSessionId) {
            args.push('--resume', this._currentSessionId);
        }
        // Create terminal with the claude /model command
        const terminal = vscode.window.createTerminal({
            name: 'Claude Model Selection',
            location: { viewColumn: vscode.ViewColumn.One }
        });
        if (wslEnabled) {
            terminal.sendText(`wsl -d ${wslDistro} ${nodePath} --no-warnings --enable-source-maps ${claudePath} ${args.join(' ')}`);
        }
        else {
            terminal.sendText(`claude ${args.join(' ')}`);
        }
        terminal.show();
        // Show info message
        vscode.window.showInformationMessage('Check the terminal to update your default model configuration. Come back to this chat here after making changes.', 'OK');
        // Send message to UI about terminal
        this._postMessage({
            type: 'terminalOpened',
            data: 'Check the terminal to update your default model configuration. Come back to this chat here after making changes.'
        });
    }
    _openUsageTerminal(usageType) {
        // Get WSL configuration
        const config = vscode.workspace.getConfiguration('claudeCodeChat');
        const wslEnabled = config.get('wsl.enabled', false);
        const wslDistro = config.get('wsl.distro', 'Ubuntu');
        const terminal = vscode.window.createTerminal({
            name: 'Claude Usage',
            location: { viewColumn: vscode.ViewColumn.One }
        });
        let command;
        if (usageType === 'plan') {
            // Plan users get live usage view
            command = 'npx -y ccusage blocks --live';
        }
        else {
            // API users get recent usage history
            command = 'npx -y ccusage blocks --recent --order desc';
        }
        if (wslEnabled) {
            terminal.sendText(`wsl -d ${wslDistro} bash -ic "${command}"`);
        }
        else {
            terminal.sendText(command);
        }
        terminal.show();
    }
    _runInstallCommand() {
        const { exec } = require('child_process');
        // Check if npm exists and node >= 18
        exec('node --version', { shell: true }, (nodeErr, nodeStdout) => {
            let useNpm = false;
            if (!nodeErr && nodeStdout) {
                // Parse version (e.g., "v18.17.0" -> 18)
                const match = nodeStdout.trim().match(/^v(\d+)/);
                if (match && parseInt(match[1], 10) >= 18) {
                    useNpm = true;
                }
            }
            let command;
            if (useNpm) {
                command = 'npm install -g @anthropic-ai/claude-code';
            }
            else if (process.platform === 'win32') {
                command = 'irm https://claude.ai/install.ps1 | iex';
            }
            else {
                command = 'curl -fsSL https://claude.ai/install.sh | sh';
            }
            // Run installation silently in the background
            exec(command, { shell: true }, (error, stdout, stderr) => {
                if (error) {
                    this._postMessage({
                        type: 'installComplete',
                        success: false,
                        error: stderr || error.message
                    });
                }
                else {
                    this._postMessage({
                        type: 'installComplete',
                        success: true
                    });
                }
            });
        });
    }
    _executeSlashCommand(command) {
        // Handle /compact in chat instead of spawning a terminal
        if (command === 'compact') {
            this._sendMessageToClaude(`/${command}`);
            return;
        }
        const config = vscode.workspace.getConfiguration('claudeCodeChat');
        const wslEnabled = config.get('wsl.enabled', false);
        const wslDistro = config.get('wsl.distro', 'Ubuntu');
        const nodePath = config.get('wsl.nodePath', '/usr/bin/node');
        const claudePath = config.get('wsl.claudePath', '/usr/local/bin/claude');
        // Build command arguments
        const args = [`/${command}`];
        // Add session resume if we have a current session
        if (this._currentSessionId) {
            args.push('--resume', this._currentSessionId);
        }
        // Create terminal with the claude command
        const terminal = vscode.window.createTerminal({
            name: `Claude /${command}`,
            location: { viewColumn: vscode.ViewColumn.One }
        });
        if (wslEnabled) {
            terminal.sendText(`wsl -d ${wslDistro} ${nodePath} --no-warnings --enable-source-maps ${claudePath} ${args.join(' ')}`);
        }
        else {
            terminal.sendText(`claude ${args.join(' ')}`);
        }
        terminal.show();
        // Show info message
        vscode.window.showInformationMessage(`Executing /${command} command in terminal. Check the terminal output and return when ready.`, 'OK');
        // Send message to UI about terminal
        this._postMessage({
            type: 'terminalOpened',
            data: `Executing /${command} command in terminal. Check the terminal output and return when ready.`,
        });
    }
    _sendPlatformInfo() {
        const platform = process.platform;
        const dismissed = this._context.globalState.get('wslAlertDismissed', false);
        // Get WSL configuration
        const config = vscode.workspace.getConfiguration('claudeCodeChat');
        const wslEnabled = config.get('wsl.enabled', false);
        this._postMessage({
            type: 'platformInfo',
            data: {
                platform: platform,
                isWindows: platform === 'win32',
                wslAlertDismissed: dismissed,
                wslEnabled: wslEnabled
            }
        });
    }
    _dismissWSLAlert() {
        this._context.globalState.update('wslAlertDismissed', true);
    }
    async _openFileInEditor(filePath) {
        try {
            const uri = vscode.Uri.file(filePath);
            const document = await vscode.workspace.openTextDocument(uri);
            await vscode.window.showTextDocument(document, vscode.ViewColumn.One);
        }
        catch (error) {
            vscode.window.showErrorMessage(`Failed to open file: ${filePath}`);
            console.error('Error opening file:', error);
        }
    }
    async _openDiffByMessageIndex(messageIndex) {
        try {
            const message = this._currentConversation[messageIndex];
            if (!message) {
                console.error('Message not found at index:', messageIndex);
                return;
            }
            const data = message.data;
            const toolName = data.toolName;
            const rawInput = data.rawInput;
            let filePath = rawInput?.file_path || '';
            let oldContent = '';
            let newContent = '';
            if (!filePath) {
                console.error('No file path found for message at index:', messageIndex);
                return;
            }
            // Read current file from disk - this is the "before" state since edit hasn't been applied yet
            try {
                const fileUri = vscode.Uri.file(filePath);
                const fileData = await vscode.workspace.fs.readFile(fileUri);
                oldContent = Buffer.from(fileData).toString('utf8');
            }
            catch {
                // File might not exist yet (for Write creating new file)
                oldContent = '';
            }
            // Compute "after" state by applying the edit to current file
            if (toolName === 'Edit' && rawInput?.old_string && rawInput?.new_string) {
                newContent = oldContent.replace(rawInput.old_string, rawInput.new_string);
            }
            else if (toolName === 'MultiEdit' && rawInput?.edits) {
                newContent = oldContent;
                for (const edit of rawInput.edits) {
                    if (edit.old_string && edit.new_string) {
                        newContent = newContent.replace(edit.old_string, edit.new_string);
                    }
                }
            }
            else if (toolName === 'Write' && rawInput?.content) {
                newContent = rawInput.content;
            }
            if (oldContent !== newContent) {
                await this._openDiffEditor(oldContent, newContent, filePath);
            }
            else {
                vscode.window.showInformationMessage('No changes to show - the edit may have already been applied.');
            }
        }
        catch (error) {
            console.error('Error opening diff by message index:', error);
        }
    }
    async _openDiffEditor(oldContent, newContent, filePath) {
        try {
            // oldContent and newContent are now full file contents passed from the webview
            const baseName = path.basename(filePath);
            const timestamp = Date.now();
            // Create unique paths for the virtual documents
            const oldPath = `/${timestamp}/old/${baseName}`;
            const newPath = `/${timestamp}/new/${baseName}`;
            // Store content in the global store for the content provider
            diffContentStore.set(oldPath, oldContent);
            diffContentStore.set(newPath, newContent);
            // Create URIs with our custom scheme
            const oldUri = vscode.Uri.parse(`claude-diff:${oldPath}`);
            const newUri = vscode.Uri.parse(`claude-diff:${newPath}`);
            // Ensure side-by-side diff mode is enabled
            const diffConfig = vscode.workspace.getConfiguration('diffEditor');
            const wasInlineMode = diffConfig.get('renderSideBySide') === false;
            if (wasInlineMode) {
                await diffConfig.update('renderSideBySide', true, vscode.ConfigurationTarget.Global);
            }
            // Open diff editor
            await vscode.commands.executeCommand('vscode.diff', oldUri, newUri, `${baseName} (Changes)`);
            // Clean up stored content when documents are closed
            const closeListener = vscode.workspace.onDidCloseTextDocument((doc) => {
                if (doc.uri.toString() === oldUri.toString()) {
                    diffContentStore.delete(oldPath);
                }
                if (doc.uri.toString() === newUri.toString()) {
                    diffContentStore.delete(newPath);
                }
                // Dispose listener when both are cleaned up
                if (!diffContentStore.has(oldPath) && !diffContentStore.has(newPath)) {
                    closeListener.dispose();
                }
            });
            this._disposables.push(closeListener);
        }
        catch (error) {
            vscode.window.showErrorMessage(`Failed to open diff editor: ${error}`);
            console.error('Error opening diff editor:', error);
        }
    }
    async _createImageFile(imageData, imageType) {
        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
                return;
            }
            // Extract base64 data from data URL
            const base64Data = imageData.split(',')[1];
            const buffer = Buffer.from(base64Data, 'base64');
            // Get file extension from image type
            const extension = imageType.split('/')[1] || 'png';
            // Create unique filename with timestamp
            const timestamp = Date.now();
            const imageFileName = `image_${timestamp}.${extension}`;
            // Create images folder in workspace .claude directory
            const imagesDir = vscode.Uri.joinPath(workspaceFolder.uri, '.claude', 'claude-code-chat-images');
            await vscode.workspace.fs.createDirectory(imagesDir);
            // Create .gitignore to ignore all images
            const gitignorePath = vscode.Uri.joinPath(imagesDir, '.gitignore');
            try {
                await vscode.workspace.fs.stat(gitignorePath);
            }
            catch {
                // .gitignore doesn't exist, create it
                const gitignoreContent = new TextEncoder().encode('*\n');
                await vscode.workspace.fs.writeFile(gitignorePath, gitignoreContent);
            }
            // Create the image file
            const imagePath = vscode.Uri.joinPath(imagesDir, imageFileName);
            await vscode.workspace.fs.writeFile(imagePath, buffer);
            // Send the file path back to webview
            this._postMessage({
                type: 'imagePath',
                data: {
                    filePath: imagePath.fsPath
                }
            });
        }
        catch (error) {
            console.error('Error creating image file:', error);
            vscode.window.showErrorMessage('Failed to create image file');
        }
    }
    dispose() {
        if (this._panel) {
            this._panel.dispose();
            this._panel = undefined;
        }
        // Dispose message handler if it exists
        if (this._messageHandlerDisposable) {
            this._messageHandlerDisposable.dispose();
            this._messageHandlerDisposable = undefined;
        }
        while (this._disposables.length) {
            const disposable = this._disposables.pop();
            if (disposable) {
                disposable.dispose();
            }
        }
    }
}
//# sourceMappingURL=extension.js.map