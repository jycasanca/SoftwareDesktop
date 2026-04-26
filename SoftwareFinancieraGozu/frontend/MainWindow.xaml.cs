using System;
using System.Diagnostics;
using System.IO;
using System.Windows;
using Microsoft.Web.WebView2.Core;

namespace SoftwareFinancieraGozu
{
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();
            InitializeWebView();
            StartBackend();
        }

        private async void InitializeWebView()
        {
            await webView.EnsureCoreWebView2Async(null);
        }

        private void StartBackend()
        {
            var appFolder = AppDomain.CurrentDomain.BaseDirectory;
            var backendScript = Path.GetFullPath(Path.Combine(appFolder, "..", "..", "..", "..", "backend", "main.py"));
            var startInfo = new ProcessStartInfo("python", $"\"{backendScript}\"")
            {
                UseShellExecute = true
            };
            Process.Start(startInfo);
        }
    }
}