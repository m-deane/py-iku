/* CSS modules and other asset types. */
declare module "*.module.css" {
  const classes: { readonly [k: string]: string };
  export default classes;
}

declare module "*.css" {
  const css: string;
  export default css;
}
