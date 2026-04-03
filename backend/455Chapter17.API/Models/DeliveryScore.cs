using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace _455chapter17.API.Models;

[Table("delivery_scores")]
public class DeliveryScore
{
    [Key]
    [Column("order_id")]
    public int OrderId { get; set; }

    [Column("late_delivery_probability")]
    public decimal LateDeliveryProbability { get; set; }

    [Column("scored_at")]
    public DateTime ScoredAt { get; set; }

    [Column("score_source")]
    public string ScoreSource { get; set; } = "";

    [Column("model_version")]
    public string ModelVersion { get; set; } = "";

    public Order? Order { get; set; }
}
