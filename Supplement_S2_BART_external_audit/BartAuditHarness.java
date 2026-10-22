import bart.model.EGTask;
import bart.model.errorgenerator.*;
import bart.model.errorgenerator.operator.*;
import bart.persistence.DAOEGTask;
import speedy.model.database.*;
import speedy.model.algebra.operators.ITupleIterator;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.file.*;
import java.io.*;
import java.util.*;

/** Observation-only harness: no generator choice, rate, seed or target mutation. */
public class BartAuditHarness {
    static final ObjectMapper JSON = new ObjectMapper();
    static Map<String,Object> val(IValue v) {
        Map<String,Object> m = new LinkedHashMap<>();
        m.put("null_reference",v==null);
        m.put("runtime_class",v==null?null:v.getClass().getName());
        m.put("text",v==null?null:v.toString());
        return m;
    }
    static Map<String,Object> snap(IDatabase db) {
        Map<String,Object> out=new LinkedHashMap<>();
        if(db==null) return out;
        for(String tn: db.getTableNames()) {
            ITable table=db.getTable(tn);
            List<Map<String,Object>> rows=new ArrayList<>();
            ITupleIterator it=table.getTupleIterator();
            while(it.hasNext()) {
                Tuple tuple=it.next();
                Map<String,Object> row=new LinkedHashMap<>();
                row.put("oid",tuple.getOid().toString());
                Map<String,Object> cells=new LinkedHashMap<>();
                for(Attribute a:table.getAttributes()) {
                    if(a.getName().equalsIgnoreCase("oid"))continue;
                    Cell c=tuple.getCell(new AttributeRef(a.getTableName(),a.getName()));
                    cells.put(a.getName(),val(c.getValue()));
                }
                row.put("cells",cells);rows.add(row);
            }
            it.close();out.put(tn,rows);
        }
        return out;
    }
    static void save(Path root,String name,Object value)throws Exception {
        JSON.writerWithDefaultPrettyPrinter().writeValue(root.resolve(name).toFile(),value);
    }
    public static void main(String[] args)throws Exception {
        if(args.length!=2)throw new IllegalArgumentException("task.xml outputdir");
        Path taskPath=Paths.get(args[0]).toAbsolutePath();
        Path out=Paths.get(args[1]).toAbsolutePath();Files.createDirectories(out);
        // XML type and absence of external configs are also checked by Python runner.
        EGTask task=new DAOEGTask().loadTask(taskPath.toString());
        if(!task.getTarget().getClass().getName().contains("MainMemory"))
            throw new IllegalStateException("Only main-memory targets authorized: "+task.getTarget().getClass());
        save(out,"clean_snapshot.json",snap(task.getTarget()));
        save(out,"source_before.json",snap(task.getSource()));
        new ExportDatabaseCSV().export(task.getTarget(),"clean",out.toString(),taskPath.toString());
        save(out,"clean_crosswalk_after_export.json",snap(task.getTarget()));
        CellChanges changes=new APrioriGenerator().run(task);
        List<Map<String,Object>> events=new ArrayList<>();
        for(ICellChange c:changes.getChanges()) {
            Map<String,Object> e=new LinkedHashMap<>();Cell cell=c.getCell();
            e.put("oid",cell.getTupleOID().toString());
            e.put("attribute",cell.getAttribute());
            e.put("cell_ref",cell.getTupleOID()+"."+cell.getAttribute());
            e.put("original",val(cell.getValue()));e.put("new",val(c.getNewValue()));
            e.put("type",c.getType());e.put("violated_dependencies",c.getViolatedDependencies());
            e.put("exported",!(c instanceof RandomCellChange)||((RandomCellChange)c).isExport());
            events.add(e);
        }
        save(out,"events_native.json",events);
        save(out,"target_after_generation.json",snap(task.getTarget()));
        save(out,"source_after.json",snap(task.getSource()));
        IDatabase dirty=task.getDirtyTarget();
        // Original samples generate events without applying them. Export the native
        // overlay on the original target when no dirty database was materialized.
        if(dirty==null) dirty=task.getTarget();
        save(out,"dirty_crosswalk_before_export.json",snap(dirty));
        new ExportCellChangesCSV().export(changes,out.resolve("events_native.csv").toString(),taskPath.toString(),false);
        new ExportDatabaseCSV().export(dirty,"dirty",changes,out.toString(),taskPath.toString());
        save(out,"dirty_crosswalk_after_export.json",snap(dirty));
        System.out.println("AUDIT_NATIVE_OBSERVATION_COMPLETE events="+events.size());
    }
}
