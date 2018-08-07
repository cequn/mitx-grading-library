// Hacky imports since we aren't transpiling
require("./MJxPrep.js")
const {
  findClosingBrace,
  replaceFunctionCalls,
  groupExpr,
  shallowListSplit,
  preProcessEqn,
  columnizeVectors,
  funcToPostfix
} = window.MJxPrepExports

describe('findClosingBrace', () => {
  it('finds the closing brace', () => {
    //                  01234567890123456789012345678901234567890123456789
    const expression = '4 + ( sin( 3^(1) - 7^2 ) + 5 ) + exp(8 - (4*3) )'
    const openIdx = 4
    expect(findClosingBrace(expression, openIdx)).toBe(29)
  } )

  it('throws an error if no opening brace at specified location', () => {
    //                  0123456789
    const expression = '4 + sin(x)'
    const openIdx = 2
    const badfunc = () => findClosingBrace(expression, openIdx)
    expect(badfunc).toThrow(
      `${expression} does not contain an opening brace at position ${openIdx}.`
    )
  } )

  it('returns null if brace opens but does not close', () => {
    //                  012345678901234
    const expression = '4 + sin( e^(2t)'
    const openIdx = 7
    expect(findClosingBrace(expression, openIdx)).toBe(null)
  } )

} )

describe('replaceFunctionCalls', () => {

  const action = (funcName, args) => `${funcName.toUpperCase()}(${args})^*`

  it('detects arguments', () => {
    const expr = "1 + cat(2, 3 + cat(1) +1 ) + 4*cat(2,3,4)"
    const result = replaceFunctionCalls(expr, 'cat', action)
    expect(result).toBe('1 + CAT(2, 3 + CAT(1)^* +1 )^* + 4*CAT(2,3,4)^*')
  } )

  it('only affects the desired functions', () => {
    const expr = "1 + acat(2, 3 + cat(1) +1 ) + 4*cats(2,3,4)"
    const result = replaceFunctionCalls(expr, 'cat', action)
    expect(result).toBe('1 + acat(2, 3 + CAT(1)^* +1 ) + 4*cats(2,3,4)')
  } )

  it('replaces closed calls, even if some func calls not closed', () => {
    const expr = 'cat(1) + cat(2, cat(3), 4'
    const result = replaceFunctionCalls(expr, 'cat', action)
    expect(result).toBe('CAT(1)^* + cat(2, CAT(3)^*, 4')
  } )

} )

describe('preProcessEqn', () => {
  it('replaces log10 and log2', () => {
    const expr = 'log10(1 + log2(x))'
    const result = preProcessEqn(expr)
    expect(result).toBe('log_10(1 + log_2(x))')
  } )

  it('replaces fact and factorial', () => {
    const expr = 'fact(n) + factorial(2n)'
    const result = preProcessEqn(expr)
    expect(result).toBe('{:n!:} + {:(2n)!:}')
  } )

  it('replaces ctrans, adj and trans', () => {
    const expr = 'ctrans(x) + adj(x+1) + trans([x, x^2])'
    const result = preProcessEqn(expr)
    expect(result).toBe('{:x^dagger:} + {:(x+1)^dagger:} + {:[[x], [ x^2]]^T:}')
  } )

  it('replaces conj based on the options', () => {
    const expr = 'conj(psi)'
    const result = preProcessEqn(expr)
    expect(result).toBe('{:psi^**:}')

    window.MJxPrepOptions.conj_as_star = false;
    const result2 = preProcessEqn(expr)
    expect(result2).toBe('conj(psi)')
  } )

  it('wraps delta and Delta appropriately', () => {
    const expr = 'DeltaE + deltasomething + delta + Delta'
    const result = preProcessEqn(expr)
    expect(result).toBe('{:DeltaE:} + {:deltasomething:} + delta + Delta')
  } )

  it('replaces cross products', () => {
    const eqn = 'cross(x) + cross(a + b, c) + y'
    expect(preProcessEqn(eqn)).toBe('cross(x) + {:(a + b) times c:} + y')
  } )
} )

describe('shallowListSplit', () => {
  it('splits a stringified list at commas where brackets are balanced', () => {
    const expr = '0, 1 + (x*[2, 3]), [[4, 5], [6, 7]]zz, 8  f'
    const expected = ['0', ' 1 + (x*[2, 3])', ' [[4, 5], [6, 7]]zz', ' 8  f']
    expect(shallowListSplit(expr)).toEqual(expected)
  } )

  it('returns the original list if it is not balanced', () => {
    const expr = '[[1, 2, 3], [1, 2, 3]'
    expect(shallowListSplit(expr)).toBe(expr)
  } )
} )

describe('groupExpr', () => {
  it('does not wrap single characters or greek letters', () => {
    expect(groupExpr('x')).toBe('x')
    expect(groupExpr('delta')).toBe('delta')
  } )
  it('does not wrap vec or hat followed by single chars or greek letters', () =>{
    expect(groupExpr('vecx')).toBe('vecx')
    expect(groupExpr('hatx')).toBe('hatx')
    expect(groupExpr('vecdelta')).toBe('vecdelta')
    expect(groupExpr('hatdelta')).toBe('hatdelta')
  } )
  it('does not wrap expression if already wrapped', () => {
    expect(groupExpr('(1)')).toBe('(1)')
    // But:
    expect(groupExpr('(1)*(2)')).toBe('((1)*(2))')
  } )
  it('removes extra whitespace before checking if already wrapped', () => {
    expect(groupExpr('  (1)  ')).toBe('(1)')
    // But:
    expect(groupExpr('  (1)*(2)  ')).toBe('((1)*(2))')
  } )

} )

describe('columnizeVectors', () => {
  it('turns vectors into column matrices and leaves matrices alone', () => {
    const expr = 'x + [1, f(a, b), 3] + [[1, 2], [3, 4]]'
    expect(columnizeVectors(expr)).toBe(
      'x + [[1], [ f(a, b)], [ 3]] + [[1, 2], [3, 4]]'
    )
  } )

  it("columnizes vectors, even when some vectors haven't been closed", () => {
    const expr = '[1, 2, 3] + [1, 2,'
    expect(columnizeVectors(expr)).toBe('[[1], [ 2], [ 3]] + [1, 2,')
  } )
} )

describe('callback returned by funcToPostfix', () => {

  it('converts unary calls, leaves other calls alone', () => {
    const daggerize = funcToPostfix('^dagger')
    const expr = 'adj(x, y) + adj(z) + 5'
    const result = replaceFunctionCalls(expr, 'adj', daggerize)
    expect(result).toBe('adj(x, y) + {:z^dagger:} + 5')
  } )
} )
