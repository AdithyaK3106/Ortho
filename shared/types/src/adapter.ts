/**
 * Language Adapter Interface
 *
 * Defines the contract for language-specific code analysis adapters.
 * Each language (Python, Kotlin, Go) implements this interface.
 */

export interface LanguageAdapter {
  /**
   * Parse a source file and return its AST.
   *
   * @param filePath - Path to the source file
   * @returns AST object (tree-sitter Tree type for Python adapter)
   */
  parse(filePath: string): any;

  /**
   * Extract symbols (functions, classes, methods) from an AST.
   *
   * @param tree - AST tree object from parse()
   * @returns Array of Symbol objects
   */
  extractSymbols(tree: any): Symbol[];

  /**
   * Extract import dependencies from an AST.
   *
   * @param tree - AST tree object from parse()
   * @returns Array of ImportEdge objects
   */
  analyzeDependencies(tree: any): ImportEdge[];
}

/**
 * Symbol represents a code symbol (function, class, method).
 */
export interface Symbol {
  name: string;
  qualifiedName: string;
  type: 'function' | 'class' | 'method';
  lineno: number;
  docstring: string | null;
}

/**
 * ImportEdge represents a dependency between modules.
 */
export interface ImportEdge {
  sourceModule: string;
  targetModule: string;
  importType: 'from' | 'import' | 'relative';
  lineno: number;
}
