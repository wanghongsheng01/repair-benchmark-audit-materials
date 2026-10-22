import bart.comparison.repairs.*;
import java.util.*;
import java.nio.file.*;
import com.fasterxml.jackson.databind.ObjectMapper;
/** Calls the original native scorer, with saved observed probe inputs. */
public class BartScorerProbe {
  static Map<String,Object> metrics(PrecisionAndRecall p) {
    Map<String,Object> r=new LinkedHashMap<>();
    r.put("precision",p.getPrecision());r.put("recall",p.getRecall());
    r.put("f1",Double.isFinite(p.getfMeasure())?p.getfMeasure():null);
    r.put("native_f1_text",Double.toString(p.getfMeasure()));return r;
  }
  public static void main(String[] args)throws Exception {
    if(args.length!=4)throw new IllegalArgumentException("expected.csv snapshot-probe.csv wiki-probe.csv output.json");
    ComputeQualityOfRepairs scorer=new ComputeQualityOfRepairs();
    Map<String,Object> out=new LinkedHashMap<>();
    for(int i=1;i<=2;i++) {
      Map<String,Object> row=new LinkedHashMap<>();
      row.put("value",metrics(scorer.calculatePrecisionAndRecallValue(args[i],args[0],0.0).get(0)));
      row.put("cell",metrics(scorer.calculatePrecisionAndRecallCell(args[i],args[0]).get(0)));
      out.put(i==1?"snapshot_clean_probe":"documented_clean_column_probe",row);
    }
    new ObjectMapper().writerWithDefaultPrettyPrinter().writeValue(Paths.get(args[3]).toFile(),out);
    System.out.println(new ObjectMapper().writeValueAsString(out));
  }
}
