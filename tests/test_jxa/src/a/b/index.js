c = Library("c");
function hello() {
  return "hello from b/index.js\n" + c.hello();
}
