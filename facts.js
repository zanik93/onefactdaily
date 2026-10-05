// Fact #1 is published on "start" (facts.json); one new fact per day (Europe/Sofia).
async function loadFacts(){
  const d=await (await fetch('facts.json')).json();
  const today=new Date().toLocaleDateString('en-CA',{timeZone:'Europe/Sofia'});
  const days=Math.floor((Date.parse(today)-Date.parse(d.start))/864e5);
  const list=d.facts.slice(0,Math.max(0,days+1)).map((f,i)=>({...f,n:i+1}));
  if(!list.length&&d.facts.length)list.push({...d.facts[0],n:1});
  return {list};
}
