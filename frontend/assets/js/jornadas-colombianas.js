/* Variantes organizadas por momento del día. Se suman a la carta existente. */
(() => {
  const seccion = (cat, emoji, color, platos) => ({ cat, emoji, color,
    platos: platos.map(([n, p]) => ({ n, p, e: emoji, d: `${cat}: especialidad colombiana`, t: 15 }))
  });

  window.BIBLIOTECA_COLOMBIA.push(
    seccion('Desayunos Colombianos', '🍳', '#F4B400', [
      ['Calentado paisa con huevo',16000],['Calentado con carne desmechada',20000],['Calentado vegetariano',15000],['Tamales con chocolate',18000],['Tamal tolimense con pan',19000],
      ['Changua bogotana',14000],['Huevos pericos con arepa',13000],['Huevos al gusto con arepa',12000],['Arepa con queso campesino',10000],['Arepa de choclo con queso',13000],
      ['Arepa e huevo',11000],['Arepa boyacense',10000],['Pandebono con chocolate',9000],['Almojabana con avena',9000],['Buñuelos con café',9000],
      ['Pan de yuca con chocolate',9000],['Cayeye costeño',15000],['Patacón con hogao y queso',14000],['Mogolla con huevo y queso',12000],['Sandwich de perico',14000],
      ['Desayuno campesino',18000],['Desayuno costeño',19000],['Desayuno fit colombiano',18000],['Fruta, yogur y granola',14000],['Waffles con arequipe',16000]
    ]),
    seccion('Almuerzos Corrientes', '🍛', '#8E44AD', [
      ['Corriente de pollo sudado',18000],['Corriente de carne en bistec',20000],['Corriente de carne molida',18000],['Corriente de chuleta de cerdo',20000],['Corriente de pescado frito',24000],
      ['Corriente de pechuga a la plancha',21000],['Corriente de pollo apanado',20000],['Corriente de pollo guisado',18000],['Corriente de albóndigas',19000],['Corriente de hígado encebollado',18000],
      ['Corriente de sobrebarriga',23000],['Corriente de chicharrón',22000],['Corriente de lomo de cerdo',22000],['Corriente de costilla BBQ',23000],['Corriente de salchicha ranchera',17000],
      ['Corriente de lentejas con huevo',16000],['Corriente de fríjoles paisas',18000],['Corriente de garbanzos',16000],['Corriente vegetariana',17000],['Corriente de arroz con pollo',19000],
      ['Corriente de pasta con pollo',19000],['Corriente de arroz atollado',21000],['Corriente de sudado de res',21000],['Corriente de sancocho',22000],['Corriente de ajiaco',23000]
    ]),
    seccion('Cenas Colombianas', '🌙', '#34495E', [
      ['Hamburguesa colombiana con papas',28000],['Perro caliente colombiano',18000],['Salchipapa especial',24000],['Arepa rellena de pollo',20000],['Arepa rellena de carne',22000],
      ['Mazorca desgranada con pollo',23000],['Picada colombiana personal',30000],['Choripán con papa criolla',18000],['Patacón con carne desmechada',24000],['Patacón con pollo',22000],
      ['Sándwich cubano colombiano',22000],['Empanadas con ají',12000],['Deditos de queso',14000],['Tacos de pollo criollo',22000],['Alitas BBQ con papas',26000]
    ])
  );
})();
