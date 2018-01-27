from . import *

VariableDeclarationKind = Enum('var', 'let', 'const')
PropertyNameKind = Enum('identifier', 'string', 'number')

AssignmentOperator = Enum(
    '=', '+=', '-=', '*=', '/=', '%=', '<<=', '>>=', '>>>=', '|=', '^=', '&='
)

BinaryOperator = Enum(
    '==', '!=', '===', '!==', '<', '<=', '>', '>=', 'in', 'instanceof', '<<',
    '>>', '>>>', '+', '-', '*', '/', '%', ',', '||', '&&', '|', '^', '&'
)

PrefixOperator = Enum('+', '-', '!', '~', 'typeof', 'void', 'delete', '++', '--')
PostfixOperator = Enum('++', '--')


class Directive(Node):
    pass


class Statement(Node):
    pass


class Expression(Node):
    pass


class FunctionBody(Node):
    directives: List(NodeRef(Directive))
    statements: List(NodeRef(Statement))


class PrimaryExpression(Expression):
    pass


class LiteralExpression(PrimaryExpression):
    pass


class PropertyName(Node):  # special case for this?
    kind: PropertyNameKind
    value: String()


class ObjectProperty(Node):
    name: NodeRef(PropertyName)


class AccessorProperty(ObjectProperty):
    body: NodeRef(FunctionBody)


# Other nodes

class Identifier(Node):
    name: String()


class Block(Node):
    statements: List(NodeRef(Statement))


class CatchClause(Node):
    binding: NodeRef(Identifier)
    body: NodeRef(Block)


class Script(Node):
    body: NodeRef(FunctionBody)


class SwitchCase(Node):
    test: NodeRef(Expression)
    consequent: List(NodeRef(Statement))


class SwitchDefault(Node):
    consequent: List(NodeRef(Statement))


class VariableDeclarator(Node):
    binding: NodeRef(Identifier)
    init: Optional(NodeRef(Expression))


class VariableDeclaration(Node):
    kind: VariableDeclarationKind
    declarators: List(NodeRef(VariableDeclarator), nonempty=True)


# Functions

class Function:
    parameters: List(NodeRef(Identifier))


class FunctionDeclaration(Function, Statement):
    name: NodeRef(Identifier)
    body: NodeRef(FunctionBody)


class FunctionExpression(Function, PrimaryExpression):
    name: Optional(NodeRef(Identifier))
    body: NodeRef(FunctionBody)


# Object expressions

class ObjectExpression(PrimaryExpression):
    properties: List(NodeRef(ObjectProperty))


class Getter(AccessorProperty):
    pass


class Setter(AccessorProperty):
    parameter: NodeRef(Identifier)


class DataProperty(ObjectProperty):
    expression: NodeRef(Expression)


# Literals

class LiteralBooleanExpression(LiteralExpression):
    value: Boolean()


class LiteralInfinityExpression(LiteralExpression): pass


class LiteralNullExpression(LiteralExpression): pass


class LiteralNumericExpression(LiteralExpression):
    value: Number()


class LiteralRegExpExpression(LiteralExpression):
    value: String()


class LiteralStringExpression(LiteralExpression):
    value: String()


# Other expressions

class ArrayExpression(PrimaryExpression):
    elements: List(Optional(NodeRef(Expression)))


class AssignmentExpression(Expression):
    operator: AssignmentOperator
    binding: NodeRef(Expression)
    expression: NodeRef(Expression)


class BinaryExpression(Expression):
    operator: BinaryOperator
    left: NodeRef(Expression)
    right: NodeRef(Expression)


class CallExpression(Expression):
    callee: NodeRef(Expression)
    arguments: List(NodeRef(Expression))


class ComputedMemberExpression(Expression):
    object: NodeRef(Expression)
    expression: NodeRef(Expression)


class ConditionalExpression(Expression):
    test: NodeRef(Expression)
    consequent: NodeRef(Expression)
    alternate: NodeRef(Expression)


class IdentifierExpression(PrimaryExpression):
    identifier: NodeRef(Identifier)


class NewExpression(Expression):
    callee: NodeRef(Expression)
    arguments: List(NodeRef(Expression))


class PostfixExpression(Expression):
    operator: PostfixOperator
    operand: NodeRef(Expression)


class PrefixExpression(Expression):
    operator: PrefixOperator
    operand: NodeRef(Expression)


class StaticMemberExpression(Expression):
    object: NodeRef(Expression)
    property: NodeRef(Identifier)


class ThisExpression(PrimaryExpression):
    pass


# Other statements

class BlockStatement(Statement):
    block: NodeRef(Block)


class BreakStatement(Statement):
    label: Optional(NodeRef(Identifier))


class ContinueStatement(Statement):
    label: Optional(NodeRef(Identifier))


class DebuggerStatement(Statement):
    pass


class DoWhileStatement(Statement):
    body: NodeRef(Statement)
    test: NodeRef(Expression)


class EmptyStatement(Statement):
    pass


class ExpressionStatement(Statement):
    expression: NodeRef(Expression)


class ForInStatement(Statement):
    left: NodeRef(VariableDeclaration, Expression)
    right: NodeRef(Expression)
    body: NodeRef(Statement)


class ForStatement(Statement):
    init: Optional(NodeRef(VariableDeclaration, Expression))
    test: Optional(NodeRef(Expression))
    update: Optional(NodeRef(Expression))
    body: NodeRef(Statement)


class IfStatement(Statement):
    test: NodeRef(Expression)
    consequent: NodeRef(Statement)
    alternate: Optional(NodeRef(Statement))


class LabeledStatement(Statement):
    label: NodeRef(Identifier)
    body: NodeRef(Statement)


class ReturnStatement(Statement):
    expression: Optional(NodeRef(Expression))


class SwitchStatement(Statement):
    discriminant: NodeRef(Expression)
    cases: List(NodeRef(SwitchCase))


class SwitchStatementWithDefault(Statement):  # ???
    discriminant: NodeRef(Expression)
    preDefaultCases: List(NodeRef(SwitchCase))
    defaultCase: NodeRef(SwitchDefault)
    postDefaultCases: List(NodeRef(SwitchCase))


class ThrowStatement(Statement):
    expression: NodeRef(Expression)


class TryCatchStatement(Statement):
    body: NodeRef(Block)
    catchClause: NodeRef(CatchClause)


class TryFinallyStatement(Statement):
    body: NodeRef(Block)
    catchClause: Optional(NodeRef(CatchClause))
    finalizer: NodeRef(Block)


class VariableDeclarationStatement(Statement):
    declaration: NodeRef(VariableDeclaration)


class WhileStatement(Statement):
    test: NodeRef(Expression)
    body: NodeRef(Statement)


class WithStatement(Statement):
    object: NodeRef(Expression)
    body: NodeRef(Statement)


# Directives

class UnknownDirective(Directive):
    value: String()


class UseStrictDirective(Directive):
    pass


# Spec meta

root_type = Script
