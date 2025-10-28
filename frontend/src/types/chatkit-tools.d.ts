declare module "@openai/chatkit" {
  interface ClientToolInvocation<TArgs = Record<string, unknown>> {
    // Projects can augment this interface to provide strongly typed arguments
    // and results for custom client tools.
    switch_theme(params: { theme: "light" | "dark" }): { success: boolean };
  }
}
