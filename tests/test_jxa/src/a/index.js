b = Library("b");
function hello() {
  return "hello from a/index.js\n" + b.hello();
}
